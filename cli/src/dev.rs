use crate::project::find_project_root;
use anyhow::{Context, Result};
use std::path::Path;
use std::process::{Command, Stdio};

pub fn run(host: &str, port: u16, no_reload: bool) -> Result<()> {
    let root = find_project_root(Path::new("."))?;
    let mut args = vec![
        "run".to_string(),
        "python".to_string(),
        "-m".to_string(),
        "rusjango._dev".to_string(),
        "--host".to_string(),
        host.to_string(),
        "--port".to_string(),
        port.to_string(),
    ];
    if no_reload {
        args.push("--no-reload".to_string());
    }

    let status = try_uv(&root, &args).or_else(|_| try_python(&root, &args))?;
    if !status.success() {
        std::process::exit(status.code().unwrap_or(1));
    }
    Ok(())
}

fn try_uv(root: &Path, args: &[String]) -> Result<std::process::ExitStatus> {
    Command::new("uv")
        .args(args)
        .current_dir(root)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status()
        .context("failed to run `uv` — install from https://docs.astral.sh/uv/")
}

fn try_python(root: &Path, args: &[String]) -> Result<std::process::ExitStatus> {
    let python_args: Vec<&str> = args
        .iter()
        .skip(1) // drop "run"
        .map(String::as_str)
        .collect();
    Command::new("python")
        .args(&python_args)
        .current_dir(root)
        .stdin(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .status()
        .context("failed to run `python`")
}
