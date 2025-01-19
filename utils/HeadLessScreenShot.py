import subprocess


# Run the Puppeteer script
def take_screen_shot(html_content):
    """
    Run the Puppeteer script to take a screenshot of the email content
    Args:
            html_content (str): The HTML content of the email
    """
    try:
        result = subprocess.run(
            ["node", "webpage.js", html_content],  # Command to execute
            capture_output=True,    # Capture stdout and stderr
            text=True               # Return output as a string
        )

        # Check if the script ran successfully
        if result.returncode == 0:
            print("Puppeteer script executed successfully!")
            print(result.stdout)  # Print the output of the script
        else:
            print("Failed to execute Puppeteer script:")
            print(result.stderr)  # Print the error message
    except Exception as e:
        print(f"An error occurred: {e}")