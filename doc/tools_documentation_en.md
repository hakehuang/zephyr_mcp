# Zephyr MCP Agent Tools Documentation

## Available Tools List

**Total number of tools:** 14

### Git Operations (14)

#### fetch_branch_or_pr
**Description:** Fetch a branch or pull request from a Git repository and checkout

Parameters:
- project_dir (str): Required. Project directory
- branch_name (Optional[str]): Optional. Branch name to fetch
- pr_number (Optional[int]): Optional. Pull request number to fetch
- remote_name (str): Optional. Remote name, default is "origin"

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** fetch_branch_or_pr module

#### get_git_config_status
**Description:** Get current Git configuration status

Parameters:
- project_dir (Optional[str]): Optional. Project directory to check local configuration

Returns:
- Dict[str, Any]: Contains Git configuration information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** get_git_config_status module

#### get_git_redirect_status
**Description:** Get current Git redirect configuration status

Parameters:
- No parameters

Returns:
- Dict[str, Any]: Contains redirect configuration status information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** get_git_redirect_status module

#### get_zephyr_status
**Description:** Get Git status information of Zephyr project

Parameters:
- project_dir (str): Required. Zephyr project directory

Returns:
- Dict[str, Any]: Contains status, current branch, commit information, etc.

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** get_zephyr_status module

#### git_checkout
**Description:** Switch to specified Git reference (SHA, tag or branch) in Zephyr project directory

Parameters:
- project_dir (str): Required. Zephyr project directory
- ref (str): Required. Git reference (SHA, tag or branch name)

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** git_checkout module

#### git_rebase
**Description:** Execute Git rebase operation

Parameters:
- project_dir (str): Required. Project directory
- source_branch (str): Required. Git reference to rebase onto (branch/tag/SHA)
- onto_branch (Optional[str]): Optional. "--onto" target (branch/tag/SHA). If None, rebases current branch onto source_branch
- interactive (bool): Optional. Whether to perform interactive rebase. Default: False
- force (bool): Optional. Whether to force rebase without confirmation. Default: False

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** git_rebase module

#### git_redirect_zephyr_mirror
**Description:** Configure Git global redirect to redirect GitHub Zephyr repository to specified mirror

Parameters:
- enable (bool): Optional. Whether to enable redirect, default is True (enabled)
- mirror_url (Optional[str]): Optional. Mirror URL, defaults to domestic mirror

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** git_redirect_zephyr_mirror module

#### run_twister
**Description:** Execute twister test or build command and return structured results

Parameters:
- platform (Optional[str]): Optional. Target hardware platform
- tests (Optional[Union[List[str], str]]): Optional. Test path or suite name (using -T parameter)
- test_cases (Optional[Union[List[str], str]]): Optional. Test case name (using -s parameter)
- enable_slow (bool): Optional. Whether to enable slow tests, default is False
- build_only (bool): Optional. Whether to build only, default is False
- extra_args (Optional[str]): Optional. Additional twister parameters
- project_dir (str): Required. Zephyr project root directory

Returns:
- Dict[str, Any]: Contains status, log, statistics and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** run_twister module

#### set_git_credentials
**Description:** Set Git credentials for authentication

Parameters:
- username (str): Required. Git username or access token
- password (str): Required. Git password or personal access token
- project_dir (Optional[str]): Optional. Project directory for local configuration

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** set_git_credentials module

#### switch_zephyr_version
**Description:** Switch to specified Zephyr version (SHA or tag) and run west update

Parameters:
- project_dir (str): Required. Zephyr project directory
- ref (str): Required. Git reference (SHA, tag or branch name)

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** switch_zephyr_version module

#### test_git_connection
**Description:** Test Git connection with provided credentials

Parameters:
- repo_url (str): Required. Git repository URL to test
- username (Optional[str]): Optional. Git username for authentication
- password (Optional[str]): Optional. Git password for authentication
- project_dir (Optional[str]): Optional. Project directory for testing

Returns:
- Dict[str, Any]: Contains status, connection test results and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** test_git_connection module

#### validate_west_init_params
**Description:** Validate west init parameters and provide helpful suggestions

Parameters:
- repo_url (Optional[str]): Git repository URL to validate
- branch (Optional[str]): Git branch name to validate
- project_dir (Optional[str]): Local project directory to validate
- auth_method (str): Authentication method to validate

Returns:
- Dict[str, Any]: Contains validation status, suggestions, and error information

Exception Handling:
- Does not throw exceptions, only returns validation results

**Return value:** []
**Source:** validate_west_init_params module

#### west_flash
**Description:** Execute west flash command to flash firmware

Parameters:
- build_dir (str): Required. Build output directory
- board (Optional[str]): Optional. Target hardware board model
- runner (Optional[str]): Optional. Flasher type (e.g., jlink, pyocd, openocd, etc.)
- probe_id (Optional[str]): Optional. Flasher ID/serial number
- flash_extra_args (Optional[str]): Optional. Additional flash parameters

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** west_flash module

#### west_update
**Description:** Run west update command in Zephyr project directory

Parameters:
- project_dir (str): Required. Zephyr project directory

Returns:
- Dict[str, Any]: Contains status, log and error information

Exception Handling:
- Tool detection failure or command execution exception will be reflected in the returned error information

**Return value:** []
**Source:** west_update module
