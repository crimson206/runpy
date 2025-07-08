import click


@click.group()
def cli():
    """Main CLI application"""
    pass


@cli.group()
def database():
    """Database management commands"""
    pass


@database.command()
def backup():
    """Create a backup of the database
    
    This creates a full backup of all tables and stores it
    in the backup directory with timestamp.
    """
    click.echo("Creating database backup...")


@database.command()
def restore():
    """Restore database from backup
    
    Restores the database from a previous backup file.
    Requires backup file path as argument.
    """
    click.echo("Restoring database...")


@cli.group()
def user():
    """User management commands"""
    pass


@user.command()
def create():
    """Create a new user account
    
    Creates a new user with the specified username and email.
    Optionally can set initial password and role.
    """
    click.echo("Creating user...")


@user.command()
def list():
    """List all users"""
    click.echo("Listing users...")


if __name__ == "__main__":
    # Example of what each help looks like:
    
    print("=== Main help (cli --help) ===")
    print("Commands:")
    print("  database  Database management commands")  # Only brief description
    print("  user      User management commands")      # Only brief description
    print()
    
    print("=== Database help (cli database --help) ===")
    print("Commands:")
    print("  backup   Create a backup of the database")  # Only first line
    print("  restore  Restore database from backup")     # Only first line
    print()
    
    print("=== Specific command help (cli database backup --help) ===")
    print("Create a backup of the database")
    print()
    print("This creates a full backup of all tables and stores it")
    print("in the backup directory with timestamp.")  # Full description shown here