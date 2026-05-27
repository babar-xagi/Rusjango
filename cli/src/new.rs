use crate::project::{
    copy_template_tree, generate_secret_key, templates_dir, validate_project_name,
};
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

    let template_root = templates_dir().join("project");
    if !template_root.is_dir() {
        bail!(
            "Project templates not found at {}",
            template_root.display()
        );
    }

    let secret_key = generate_secret_key();
    fs::create_dir_all(&target).context("create project directory")?;
    copy_template_tree(&template_root, &target, name, &secret_key)?;

    println!("Created Rusjango project: {}", target.display());
    println!();
    println!("  cd {}", target.display());
    println!("  uv sync");
    println!("  rusjango dev");
    Ok(())
}
