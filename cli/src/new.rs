use crate::project::{generate_secret_key, validate_project_name, write_templates};
use anyhow::{bail, Context, Result};
use std::fs;
use std::path::Path;

pub fn run(name: &str, directory: Option<&Path>) -> Result<()> {
    validate_project_name(name)?;

    let target = directory
        .map(|p| p.join(name))
        .unwrap_or_else(|| Path::new(name).to_path_buf());

    if target.exists() {
        bail!("Directory already exists: {}", target.display());
    }

    let secret_key = generate_secret_key();
    fs::create_dir_all(&target).context("create project directory")?;
    write_templates("project", &target, name, &secret_key)?;

    println!("Created Rusjango project: {}", target.display());
    println!();
    println!("  cd {}", target.display());
    println!("  uv sync");
    println!("  rusjango dev");
    Ok(())
}
