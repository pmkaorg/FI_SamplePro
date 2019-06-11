## ExecPythonScript file.py
## will activate virtual python environment in ..\VirtualEnv 
## Will execute file.py located in ..\Source of ExecPythonScript.ps1
## If there is any error an email will be sent to support_email as defined in config.ini
## uses smtpserver and send_email_from defined in config.ini 

function Get-IniFile 
{  
    param(  
        [parameter(Mandatory = $true)] [string] $filePath  
    )  

    $anonymous = "NoSection"

    $ini = @{}  
    switch -regex -file $filePath  
    {  
        "^\[(.+)\]$" # Section  
        {  
            $section = $matches[1]  
            $ini[$section] = @{}  
            $CommentCount = 0  
        }  

        "^(;.*)$" # Comment  
        {  
            if (!($section))  
            {  
                $section = $anonymous  
                $ini[$section] = @{}  
            }  
            $value = $matches[1]  
            $CommentCount = $CommentCount + 1  
            $name = "Comment" + $CommentCount  
            $ini[$section][$name] = $value  
        }   

        "(.+?)\s*=\s*(.*)" # Key  
        {  
            if (!($section))  
            {  
                $section = $anonymous  
                $ini[$section] = @{}  
            }  
            $name,$value = $matches[1..2]  
            $ini[$section][$name] = $value  
        }  
    }  

    return $ini  
}  

$root = (get-item $PSScriptRoot).parent.FullName
$py = $args[0]
# Write-Output $py

#retrieve support_email from config.ini
$iniFile = Get-IniFile "$root\config.ini"
$smtpTo = $iniFile.System.support_email
if ([string]::IsNullOrEmpty($smtpTo)) {
    $smptTo = 'wayne.schou@scionresearch.com'
}

#activate virtualenv
& "$root\VirtualEnv\Scripts\activate.ps1"

Try {
    # execute python code keeping error messages
    $err = python "$root\Source\$py" 2>&1
    if($LASTEXITCODE -ne 0) 
    { #if python execution failed return an error
        throw [System.Exception] (Out-String -InputObject $err)
    }
}
Catch {
    # email any exception to support_email
    $ErrorMessage = $_.Exception.Message
    $smtpServer = $iniFile.MailServer.smtpserver
    $smtpFrom = $iniFile.System.send_email_from
    $smtpSubject = “SamplePro Script error”
    $smtpBody = “[$(Get-Date -Format "dd/MM/yyyy HH:mm:ss")] `n$ErrorMessage”
    Send-MailMessage -From $smtpFrom -to $smtpTo -Subject $smtpSubject -Body $smtpBody -SmtpServer $smtpServer
}
Finally {
    deactivate
    exit $LASTEXITCODE
}
