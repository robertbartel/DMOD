# About

This directory contains several ngen realization config file examples useful for different QA-related tasks, along with required BMI init config files.  Details on these are provided below.  Note that while an example may have been created for a particular purpose, its use is (generally speaking) not limited to just that scenario.


# Example Configs

## File Summary

| File                | Included BMI Modules        | Forcing | Routing | Num Cats | Duration | Notes |
|---------------------|-----------------------------|---------|---------|----------|----------|-------|
| memcheck_ex_01.json | Sloth, Noah-OWP, CFE-S      | CSV     | Yes     | 3        | 1 month  |       |
| memcheck_ex_02.json | Sloth, Noah-OWP, PET, CFE-S | CSV     | No      | 3        | 1 month  |       |

## Module Usage Summary

| Module                   | Utilizing Files                          |
|--------------------------|------------------------------------------|
| **CFE-S**                | memcheck_ex_01.json, memcheck_ex_02.json |
| **CFE-X**                |                                          |
| **LGAR**                 |                                          |
| **LSTM**                 |                                          |
| **Noah-OWP**             | memcheck_ex_01.json, memcheck_ex_02.json |
| **PET**                  | memcheck_ex_02.json                      |
| **Sac-SMA**              |                                          |
| **Sloth**                | memcheck_ex_01.json, memcheck_ex_02.json |
| **Snow-17**              |                                          |
| **SoilFreezeThaw**       |                                          |
| **SoilMoistureProfiles** |                                          |
| **TopModel**             |                                          |
| **UEB**                  |                                          |


