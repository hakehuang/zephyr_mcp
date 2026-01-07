# Zephyr MCP Agent 工具文档

## 可用工具列表

**总工具数量:** 14

### Git Operations (14)

#### fetch_branch_or_pr
**描述:** Function Description: Fetch a branch or pull request from a Git repository and checkout
功能描述: 从Git仓库获取分支或拉取请求并检出

Parameters:
参数说明:
- project_dir (str): Required. Project directory
- project_dir (str): 必须。项目目录
- branch_name (Optional[str]): Optional. Branch name to fetch
- branch_name (Optional[str]): 可选。要获取的分支名称
- pr_number (Optional[int]): Optional. Pull request number to fetch
- pr_number (Optional[int]): 可选。要获取的拉取请求编号
- remote_name (str): Optional. Remote name, default is "origin"
- remote_name (str): 可选。远程仓库名称，默认为"origin"

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** fetch_branch_or_pr 模块

#### get_git_config_status
**描述:** Function Description: Get current Git configuration status
功能描述: 获取当前Git配置状态

Parameters:
参数说明:
- project_dir (Optional[str]): Optional. Project directory to check local configuration
- project_dir (Optional[str]): 可选。项目目录，用于检查本地配置

Returns:
返回值:
- Dict[str, Any]: Contains Git configuration information
- Dict[str, Any]: 包含Git配置信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** get_git_config_status 模块

#### get_git_redirect_status
**描述:** Function Description: Get current Git redirect configuration status
功能描述: 获取当前Git重定向配置状态

Parameters:
参数说明:
- No parameters
- 无参数

Returns:
返回值:
- Dict[str, Any]: Contains redirect configuration status information
- Dict[str, Any]: 包含重定向配置状态信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** get_git_redirect_status 模块

#### get_zephyr_status
**描述:** Function Description: Get Git status information of Zephyr project
功能描述: 获取Zephyr项目的Git状态信息

Parameters:
参数说明:
- project_dir (str): Required. Zephyr project directory
- project_dir (str): 必须。Zephyr项目目录

Returns:
返回值:
- Dict[str, Any]: Contains status, current branch, commit information, etc.
- Dict[str, Any]: 包含状态、当前分支、提交信息等

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** get_zephyr_status 模块

#### git_checkout
**描述:** Function Description: Switch to specified Git reference (SHA, tag or branch) in Zephyr project directory
功能描述: 在Zephyr项目目录中切换到指定的Git引用（SHA号、tag或分支）

Parameters:
参数说明:
- project_dir (str): Required. Zephyr project directory
- project_dir (str): 必须。Zephyr项目目录
- ref (str): Required. Git reference (SHA, tag or branch name)
- ref (str): 必须。Git引用（SHA号、tag或分支名称）

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** git_checkout 模块

#### git_rebase
**描述:** Function Description: Execute Git rebase operation
功能描述: 执行Git rebase操作

Parameters:
参数说明:
- project_dir (str): Required. Project directory
- project_dir (str): 必须。项目目录
- source_branch (str): Required. Git reference to rebase onto (branch/tag/SHA)
- source_branch (str): 必须。要rebase到的Git引用（分支/标签/SHA）
- onto_branch (Optional[str]): Optional. "--onto" target (branch/tag/SHA). If None, rebases current branch onto source_branch
- onto_branch (Optional[str]): 可选。"--onto" 目标（分支/标签/SHA）。如果为None，则将当前分支rebase到source_branch上
- interactive (bool): Optional. Whether to perform interactive rebase. Default: False
- interactive (bool): 可选。是否执行交互式rebase。默认：False
- force (bool): Optional. Whether to force rebase without confirmation. Default: False
- force (bool): 可选。是否强制rebase而不进行确认。默认：False

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** git_rebase 模块

#### git_redirect_zephyr_mirror
**描述:** Function Description: Configure Git global redirect to redirect GitHub Zephyr repository to specified mirror
功能描述: 配置Git全局重定向，将GitHub的Zephyr仓库地址重定向到指定的镜像源

Parameters:
参数说明:
- enable (bool): Optional. Whether to enable redirect, default is True (enabled)
- enable (bool): 可选。是否启用重定向，默认为True（启用）
- mirror_url (Optional[str]): Optional. Mirror URL, defaults to domestic mirror
- mirror_url (Optional[str]): 可选。镜像源地址，默认为国内镜像源

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** git_redirect_zephyr_mirror 模块

#### run_twister
**描述:** Function Description: Execute twister test or build command and return structured results
功能描述: 执行twister测试或编译命令并返回结构化结果

Parameters:
参数说明:
- platform (Optional[str]): Optional. Target hardware platform
- platform (Optional[str]): 可选。目标硬件平台
- tests (Optional[Union[List[str], str]]): Optional. Test path or suite name (using -T parameter)
- tests (Optional[Union[List[str], str]]): 可选。测试路径或套件名称（使用-T参数）
- test_cases (Optional[Union[List[str], str]]): Optional. Test case name (using -s parameter)
- test_cases (Optional[Union[List[str], str]]): 可选。测试用例名称（使用-s参数）
- enable_slow (bool): Optional. Whether to enable slow tests, default is False
- enable_slow (bool): 可选。是否启用慢测试，默认为False
- build_only (bool): Optional. Whether to build only, default is False
- build_only (bool): 可选。是否仅编译，默认为False
- extra_args (Optional[str]): Optional. Additional twister parameters
- extra_args (Optional[str]): 可选。额外的twister参数
- project_dir (str): Required. Zephyr project root directory
- project_dir (str): 必须。Zephyr项目根目录

Returns:
返回值:
- Dict[str, Any]: Contains status, log, statistics and error information
- Dict[str, Any]: 包含状态、日志、统计信息和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** run_twister 模块

#### set_git_credentials
**描述:** Function Description: Set Git credentials for authentication
功能描述: 设置Git认证凭据

Parameters:
参数说明:
- username (str): Required. Git username or access token
- username (str): 必须。Git用户名或访问令牌
- password (str): Required. Git password or personal access token
- password (str): 必须。Git密码或个人访问令牌
- project_dir (Optional[str]): Optional. Project directory for local configuration
- project_dir (Optional[str]): 可选。项目目录，用于本地配置

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** set_git_credentials 模块

#### switch_zephyr_version
**描述:** Function Description: Switch to specified Zephyr version (SHA or tag) and run west update
功能描述: 切换到指定的Zephyr版本（SHA号或tag）并运行west update

Parameters:
参数说明:
- project_dir (str): Required. Zephyr project directory
- project_dir (str): 必须。Zephyr项目目录
- ref (str): Required. Git reference (SHA, tag or branch name)
- ref (str): 必须。Git引用（SHA号、tag或分支名称）

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** switch_zephyr_version 模块

#### test_git_connection
**描述:** Function Description: Test Git connection with provided credentials
功能描述: 使用提供的凭据测试Git连接

Parameters:
参数说明:
- repo_url (str): Required. Git repository URL to test
- repo_url (str): 必须。要测试的Git仓库地址
- username (Optional[str]): Optional. Git username for authentication
- username (Optional[str]): 可选。Git认证用户名
- password (Optional[str]): Optional. Git password for authentication
- password (Optional[str]): 可选。Git认证密码
- project_dir (Optional[str]): Optional. Project directory for testing
- project_dir (Optional[str]): 可选。项目目录，用于测试

Returns:
返回值:
- Dict[str, Any]: Contains status, connection test results and error information
- Dict[str, Any]: 包含状态、连接测试结果和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** test_git_connection 模块

#### validate_west_init_params
**描述:** Function Description: Validate west init parameters and provide helpful suggestions
功能描述: 验证west init参数并提供有用的建议

Parameters:
参数说明:
- repo_url (Optional[str]): Git repository URL to validate
- repo_url (Optional[str]): Git仓库地址用于验证
- branch (Optional[str]): Git branch name to validate
- branch (Optional[str]): Git分支名称用于验证
- project_dir (Optional[str]): Local project directory to validate
- project_dir (Optional[str]): 本地项目目录用于验证
- auth_method (str): Authentication method to validate
- auth_method (str): 认证方法用于验证

Returns:
返回值:
- Dict[str, Any]: Contains validation status, suggestions, and error information
- Dict[str, Any]: 包含验证状态、建议和错误信息

Exception Handling:
异常处理:
- Does not throw exceptions, only returns validation results
- 不抛出异常，仅返回验证结果

**返回值:** []
**来源:** validate_west_init_params 模块

#### west_flash
**描述:** Function Description: Execute west flash command to flash firmware
功能描述: 执行west flash命令烧录固件

Parameters:
参数说明:
- build_dir (str): Required. Build output directory
- build_dir (str): 必须。构建输出目录
- board (Optional[str]): Optional. Target hardware board model
- board (Optional[str]): 可选。目标硬件板型号
- runner (Optional[str]): Optional. Flasher type (e.g., jlink, pyocd, openocd, etc.)
- runner (Optional[str]): 可选。烧录器类型（如jlink, pyocd, openocd等）
- probe_id (Optional[str]): Optional. Flasher ID/serial number
- probe_id (Optional[str]): 可选。烧录器ID/序列号
- flash_extra_args (Optional[str]): Optional. Additional flash parameters
- flash_extra_args (Optional[str]): 可选。额外的flash参数

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** west_flash 模块

#### west_update
**描述:** Function Description: Run west update command in Zephyr project directory
功能描述: 在Zephyr项目目录中运行west update命令

Parameters:
参数说明:
- project_dir (str): Required. Zephyr project directory
- project_dir (str): 必须。Zephyr项目目录

Returns:
返回值:
- Dict[str, Any]: Contains status, log and error information
- Dict[str, Any]: 包含状态、日志和错误信息

Exception Handling:
异常处理:
- Tool detection failure or command execution exception will be reflected in the returned error information
- 工具检测失败或命令执行异常会体现在返回的错误信息中

**返回值:** []
**来源:** west_update 模块
