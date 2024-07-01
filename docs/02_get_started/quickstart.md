# Quickstart

- [ ] How to setup a robotframework project with RobotCode
  - [ ] Create Virtual Environment
    - [ ] install robotframework
    - [ ] install additional tools
       - [ ] robotframework-robocop
       - [ ] robotframework-tidy
    - [ ] create your first suite/test
    - [ ] run your first test

    - [ ] configure your robotframework project
      - [ ] default settings in robot.toml
        - python-path = ["resources", "lib"]
        - output-dir = "reports"

Welcome to RobotCode! In this section we will get your Visual Studio Code set up and go through the basics: installing the extension, setting up your environment, and verifying everything is working smoothly.

## Requirements
Make sure you have **Python 3.8** or greater installed.

## Installing RobotCode
1. Open Visual Studio Code.
2. Go to the **Extensions** tab (or press `CTRL + SHIFT + X`).
3. Search for **RobotCode** and install the extension ![RobotCode Icon](../robotcode-logo.svg "RobotCode Icon"){.inline-icon} [RobotCode - Robot Framework Support](https://marketplace.visualstudio.com/items?itemName=d-biehl.robotcode "RobotCode Extension"). This will also install the **Python** and **Python Debugger** extensions.
4. **(Optional)** Install the **Even Better TOML** extension for handling `.toml` files more effectively. We'll use a `robot.toml` file in the [Configuration](./configuration) section to set up our project settings.  

After installation:
   - Right-click on the RobotCode extension in the Extensions tab.
   - Click **Add to Workspace Recommendations** to ensure that all team members working on this project are prompted to install the RobotCode extension, creating a consistent development environment for everyone.

## Initialize an Empty Project

1. **Create a `requirements.txt` file** in the root folder of your project and add the following dependencies:
::: code-group
```txt:line-numbers [requirements.txt]
robotframework
robotframework-tidy
```
:::

2. **Set up your Python environment:**
- Click on **Create Environment** in Visual Studio Code. If this button isn't visible, you can alternatively open the Command Palette by pressing `CTRL + SHIFT + P`, then search for **Python: Create Environment**, and select it.
- Choose **Venv**, which stands for Virtual Environment.
- Select your Python version.
- Check the box for requirements.txt and click OK.

## Verifying the Installation
1. Open the terminal in Visual Studio Code. Make sure you are located in the root folder of your project.
2. Run the command `robot --version` to check if Robot Framework is installed correctly.

If there are no errors, you’re all set!

## Create and Run Your First Suite/Test
Create a `first.robot` file in your project with the following code to demonstrate a basic example of logging a string message to the debug console:
::: code-group
```robot:line-numbers [first.robot]
*** Test Cases ***
First Test Case
    Log    Hello world

```
:::

To run this test file, press the green play button next to the `First Test Case` keyword in the code.
You should see the `Hello world` output displayed in the **Debug Console** of Visual Studio Code.

And that's it! If you have any questions or run into issues, check out the RobotCode documentation or join our community in slack for support. Happy coding!
