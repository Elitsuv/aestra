use std::ffi::CString;

#[derive(Debug)]
pub struct RawExecutionResult {
    pub status: String,
    pub exit_code: i32,
    pub cpu_time_ms: f64,
    pub peak_memory_bytes: u64,
    pub stdout: String,
    pub stderr: String,
    pub error_message: Option<String>,
}

pub fn execute_posix(
    command: &str,
    args: &[String],
    input_data: &str,
    time_limit_ms: u64,
    memory_limit_mb: u64,
    output_limit_bytes: usize,
) -> RawExecutionResult {
    unsafe {
        let mut stdin_pipe: [libc::c_int; 2] = [0, 0];
        let mut stdout_pipe: [libc::c_int; 2] = [0, 0];
        let mut stderr_pipe: [libc::c_int; 2] = [0, 0];

        if libc::pipe(stdin_pipe.as_mut_ptr()) < 0
            || libc::pipe(stdout_pipe.as_mut_ptr()) < 0
            || libc::pipe(stderr_pipe.as_mut_ptr()) < 0
        {
            return RawExecutionResult {
                status: "INTERNAL_ERROR".to_string(),
                exit_code: 1,
                cpu_time_ms: 0.0,
                peak_memory_bytes: 0,
                stdout: "".to_string(),
                stderr: "".to_string(),
                error_message: Some("Failed to create POSIX IPC pipes".to_string()),
            };
        }

        let pid = libc::fork();

        if pid < 0 {
            return RawExecutionResult {
                status: "INTERNAL_ERROR".to_string(),
                exit_code: 1,
                cpu_time_ms: 0.0,
                peak_memory_bytes: 0,
                stdout: "".to_string(),
                stderr: "".to_string(),
                error_message: Some("POSIX fork() system call failed".to_string()),
            };
        }

        if pid == 0 {
            let cpu_seconds = (time_limit_ms / 1000) + 1;
            let rlim_cpu = libc::rlimit {
                rlim_cur: cpu_seconds as libc::rlim_t,
                rlim_max: (cpu_seconds + 1) as libc::rlim_t,
            };
            libc::setrlimit(libc::RLIMIT_CPU, &rlim_cpu);

            let memory_bytes = memory_limit_mb * 1024 * 1024;
            let rlim_mem = libc::rlimit {
                rlim_cur: memory_bytes as libc::rlim_t,
                rlim_max: memory_bytes as libc::rlim_t,
            };
            libc::setrlimit(libc::RLIMIT_AS, &rlim_mem);

            libc::dup2(stdin_pipe[0], libc::STDIN_FILENO);
            libc::dup2(stdout_pipe[1], libc::STDOUT_FILENO);
            libc::dup2(stderr_pipe[1], libc::STDERR_FILENO);

            libc::close(stdin_pipe[1]);
            libc::close(stdout_pipe[0]);
            libc::close(stderr_pipe[0]);

            let c_cmd = match CString::new(command) {
                Ok(c) => c,
                Err(_) => libc::_exit(1),
            };

            let mut c_args: Vec<CString> = Vec::new();
            c_args.push(c_cmd.clone());
            for arg in args {
                if let Ok(c) = CString::new(arg.as_str()) {
                    c_args.push(c);
                }
            }

            let mut c_args_ptrs: Vec<*const libc::c_char> =
                c_args.iter().map(|c| c.as_ptr()).collect();
            c_args_ptrs.push(std::ptr::null());

            let env_ptrs: [*const libc::c_char; 1] = [std::ptr::null()];

            libc::execve(c_cmd.as_ptr(), c_args_ptrs.as_ptr(), env_ptrs.as_ptr());
            libc::_exit(127);
        }

        libc::close(stdin_pipe[0]);
        libc::close(stdout_pipe[1]);
        libc::close(stderr_pipe[1]);

        if !input_data.is_empty() {
            let bytes = input_data.as_bytes();
            libc::write(
                stdin_pipe[1],
                bytes.as_ptr() as *const libc::c_void,
                bytes.len(),
            );
        }
        libc::close(stdin_pipe[1]);

        let mut stdout_buf = Vec::new();
        let mut stderr_buf = Vec::new();
        let mut buf = [0u8; 4096];

        loop {
            let n = libc::read(
                stdout_pipe[0],
                buf.as_mut_ptr() as *mut libc::c_void,
                buf.len(),
            );
            if n <= 0 {
                break;
            }
            if stdout_buf.len() < output_limit_bytes {
                stdout_buf.extend_from_slice(&buf[..n as usize]);
            }
        }
        libc::close(stdout_pipe[0]);

        loop {
            let n = libc::read(
                stderr_pipe[0],
                buf.as_mut_ptr() as *mut libc::c_void,
                buf.len(),
            );
            if n <= 0 {
                break;
            }
            if stderr_buf.len() < output_limit_bytes {
                stderr_buf.extend_from_slice(&buf[..n as usize]);
            }
        }
        libc::close(stderr_pipe[0]);

        let mut status: libc::c_int = 0;
        let mut rusage: libc::rusage = std::mem::zeroed();

        libc::wait4(pid, &mut status, 0, &mut rusage);

        let user_cpu_ms = (rusage.ru_utime.tv_sec as f64 * 1000.0)
            + (rusage.ru_utime.tv_usec as f64 / 1000.0);
        let sys_cpu_ms = (rusage.ru_stime.tv_sec as f64 * 1000.0)
            + (rusage.ru_stime.tv_usec as f64 / 1000.0);
        let total_cpu_time_ms = user_cpu_ms + sys_cpu_ms;

        let peak_memory_bytes = (rusage.ru_maxrss as u64) * 1024;

        let mut status_str = "OK".to_string();
        let mut exit_code = 0;

        if libc::WIFEXITED(status) {
            exit_code = libc::WEXITSTATUS(status);
            if exit_code != 0 {
                status_str = "RUNTIME_ERROR".to_string();
            }
        } else if libc::WIFSIGNALED(status) {
            let sig = libc::WTERMSIG(status);
            exit_code = 128 + sig;
            if sig == libc::SIGXCPU || sig == libc::SIGKILL {
                status_str = "TIME_LIMIT_EXCEEDED".to_string();
            } else if sig == libc::SIGSEGV {
                if peak_memory_bytes >= (memory_limit_mb * 1024 * 1024) {
                    status_str = "MEMORY_LIMIT_EXCEEDED".to_string();
                } else {
                    status_str = "RUNTIME_ERROR".to_string();
                }
            } else {
                status_str = "RUNTIME_ERROR".to_string();
            }
        }

        if total_cpu_time_ms > (time_limit_ms as f64) {
            status_str = "TIME_LIMIT_EXCEEDED".to_string();
        }

        RawExecutionResult {
            status: status_str,
            exit_code,
            cpu_time_ms: total_cpu_time_ms,
            peak_memory_bytes,
            stdout: String::from_utf8_lossy(&stdout_buf).to_string(),
            stderr: String::from_utf8_lossy(&stderr_buf).to_string(),
            error_message: None,
        }
    }
}

