use pyo3::prelude::*;

mod sandbox_posix;

#[pyfunction]
fn execute_native(
    py: Python<'_>,
    command: String,
    args: Vec<String>,
    input_data: String,
    time_limit_ms: u64,
    memory_limit_mb: u64,
) -> PyResult<PyObject> {
    let result = py.allow_threads(|| {
        sandbox_posix::execute_posix(
            &command,
            &args,
            &input_data,
            time_limit_ms,
            memory_limit_mb,
            64 * 1024 * 1024,
        )
    });

    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("status", result.status)?;
    dict.set_item("exit_code", result.exit_code)?;
    dict.set_item("cpu_time_ms", result.cpu_time_ms)?;
    dict.set_item("peak_memory_bytes", result.peak_memory_bytes)?;
    dict.set_item("stdout", result.stdout)?;
    dict.set_item("stderr", result.stderr)?;
    dict.set_item("error_message", result.error_message)?;

    Ok(dict.into())
}

#[pymodule]
fn aestra_core(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(execute_native, m)?)?;
    Ok(())
}

