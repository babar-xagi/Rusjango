mod add;
mod dev;
mod new;
mod orm;
mod project;
mod remove;
mod settings;

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(
    name = "rusjango",
    version,
    about = "Rusjango — Rust-powered async Python framework"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Create a new minimal Rusjango project
    New {
        /// Project name
        name: String,
        /// Destination directory (default: ./<name>)
        #[arg(short, long)]
        directory: Option<PathBuf>,
    },
    /// Run the development server
    Dev {
        /// Host to bind
        #[arg(long, default_value = "127.0.0.1")]
        host: String,
        /// Port to bind
        #[arg(long, default_value = "8000")]
        port: u16,
        /// Disable auto-reload
        #[arg(long)]
        no_reload: bool,
    },
    /// Add a feature or app to the project
    Add {
        #[command(subcommand)]
        target: AddTarget,
    },
    /// Remove a feature or app from the project
    Remove {
        #[command(subcommand)]
        target: RemoveTarget,
    },
    /// Apply database migrations (create tables)
    Migrate,
}

#[derive(Subcommand)]
enum AddTarget {
    /// Add an application package under apps/
    App { name: String },
    /// Enable async ORM (SQLite by default)
    Orm,
}

#[derive(Subcommand)]
enum RemoveTarget {
    /// Remove an application package
    App {
        name: String,
        /// Skip confirmation prompt
        #[arg(long, short = 'y')]
        yes: bool,
    },
    /// Disable ORM (keeps model files and migrations/)
    Orm {
        #[arg(long, short = 'y')]
        yes: bool,
    },
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let cli = Cli::parse();
    match cli.command {
        Commands::New { name, directory } => {
            new::run(&name, directory.as_deref())?;
        }
        Commands::Dev {
            host,
            port,
            no_reload,
        } => {
            dev::run(&host, port, no_reload)?;
        }
        Commands::Migrate => orm::run_migrate()?,
        Commands::Add { target } => match target {
            AddTarget::App { name } => add::run(&name)?,
            AddTarget::Orm => orm::add_orm()?,
        },
        Commands::Remove { target } => match target {
            RemoveTarget::App { name, yes } => remove::run(&name, yes)?,
            RemoveTarget::Orm { yes } => orm::remove_orm(yes)?,
        },
    }
    Ok(())
}
