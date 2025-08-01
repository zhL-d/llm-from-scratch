use pyo3::prelude::*;

/// A simple add function to test Rust ↔ Python
#[pyfunction]
fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// This is the module entrypoint for Python
#[pymodule]
fn rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add, m)?)?;
    Ok(())
}