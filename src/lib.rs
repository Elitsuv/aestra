use pyo3::prelude::*;

/// Rust native execution function exposed to Python via PyO3 FFI.
#[pyfunction]
fn execute_native(
    command: String,
    args: Vec<String>,
    time_limit_ms: u64,
    memory_limit_mb: u64,
) -> PyResult<String> {
    Ok(format!(
        "aestra_core Rust FFI active. Command: '{}', Args: {:?}, Limits: {}ms / {}MB",
        command, args, time_limit_ms, memory_limit_mb
    ))
}

/// PyO3 Module definition for aestra_core.
#[pymodule]
fn aestra_core(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(execute_native, m)?)?;
    Ok(())
}
