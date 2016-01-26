import climax


@climax.command()
@climax.argument('--username', '-u', required=True, help='your username')
@climax.argument('--password', '-p', action=climax.PasswordPrompt,
                 required=True, help='prompt for your password')
def login(username, password):
    """Login example."""
    print(username, password)


if __name__ == '__main__':
    login()
