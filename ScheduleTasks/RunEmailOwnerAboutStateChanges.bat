@echo off
call "C:\SamplePro\VirtualEnv\Scripts\activate.bat"
python "C:\SamplePro\Source\FreezerPro\EmailOwnerAboutStateChanges.py"
call "C:\SamplePro\VirtualEnv\Scripts\deactivate.bat"
