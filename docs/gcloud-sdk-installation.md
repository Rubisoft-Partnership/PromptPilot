# Installing Google Cloud SDK

For macOS:

Using Homebrew (Recommended)

If you have Homebrew installed, you can install the Google Cloud SDK with a single command.

	1.	Install the Google Cloud SDK:

brew install --cask google-cloud-sdk


	2.	Initialize the SDK:

gcloud init

	•	Follow the prompts to log in to your Google account and set your default project.

Manual Installation

	1.	Download the SDK:
	•	Visit the Google Cloud SDK Install Page and download the macOS 64-bit package.
	2.	Extract the Archive:

tar -xzf google-cloud-sdk-*-darwin-x86_64.tar.gz


	3.	Run the Installer:

./google-cloud-sdk/install.sh


	4.	Initialize the SDK:

gcloud init



For Linux:

	1.	Download the SDK:

curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-$(curl -s https://dl.google.com/dl/cloudsdk/channels/rapid/components-2.json | grep '"version":' | head -1 | awk -F '"' '{print $4}')-linux-x86_64.tar.gz

	•	Alternatively, download it directly from the Google Cloud SDK Install Page.

	2.	Extract the Archive:

tar -xf google-cloud-sdk-*-linux-x86_64.tar.gz


	3.	Run the Installer:

./google-cloud-sdk/install.sh

	•	You may be prompted to update your .bashrc or .zshrc file to include Cloud SDK command-line tools in your PATH.

	4.	Restart Your Shell (if necessary):

exec -l $SHELL


	5.	Initialize the SDK:

gcloud init



For Windows:

	1.	Download the Installer:
	•	Visit the Google Cloud SDK Install Page and download the Windows Installer.
	2.	Run the Installer:
	•	Double-click the downloaded installer (GoogleCloudSDKInstaller.exe).
	•	Follow the installation wizard steps.
	•	Make sure to select “Install Bundled Python” if you don’t have Python installed.
	•	Optionally, select “Add gcloud to PATH” to access Cloud SDK commands in your command prompt.
	3.	Open Command Prompt or PowerShell:
	•	Press Win + R, type cmd, and press Enter.
	4.	Initialize the SDK:

gcloud init



Post-Installation Steps:

Authenticate with Google Cloud:

	1.	Log In to Your Google Account:

gcloud auth login

	•	A browser window will open for you to log in.

	2.	Set Your Default Project:

gcloud config set project YOUR_PROJECT_ID

	•	Replace YOUR_PROJECT_ID with your actual Google Cloud project ID.

Verify the Installation:

	•	Check the installed components:

gcloud components list


	•	Update components (if necessary):

gcloud components update



Additional Notes:

	•	Updating the SDK:
	•	You can update the Google Cloud SDK to the latest version with:

gcloud components update


	•	Add SDK Tools to Your PATH (if not done during installation):
	•	For Bash:
Add the following to your ~/.bashrc or ~/.bash_profile:

source ~/google-cloud-sdk/path.bash.inc
source ~/google-cloud-sdk/completion.bash.inc


	•	For Zsh:
Add the following to your ~/.zshrc:

source ~/google-cloud-sdk/path.zsh.inc
source ~/google-cloud-sdk/completion.zsh.inc


	•	Using Python 3:
	•	The Cloud SDK requires Python. If you have multiple Python versions, you can specify the Python interpreter:

gcloud config set python /usr/bin/python3