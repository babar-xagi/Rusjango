//! Rusjango core: routing, request handling, and JSON responses.
//! Python bindings are exposed via PyO3 from `rusjango._core`.

use pyo3::prelude::*;

mod router;

/// Python module: `rusjango._core`
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_function(wrap_pyfunction!(router::route_count, m)?)?;
    m.add(
        "__doc__",
        "Rusjango Rust core (routing acceleration in future releases)",
    )?;
    Ok(())
}
