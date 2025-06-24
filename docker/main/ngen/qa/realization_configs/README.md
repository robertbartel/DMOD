# About

This directory contains several ngen realization config file examples useful for different QA-related tasks, along with required BMI init config files.  Details on these are provided below.  Note that while an example may have been created for a particular purpose, its use is (generally speaking) not limited to just that scenario.


# Example Configs

## File Summary

| File                | Included BMI Modules        | Forcing | Hydrofabric | Routing | Num Cats | Duration | Notes |
|---------------------|-----------------------------|---------|-------------|---------|----------|----------|-------|
| memcheck_ex_01.json | Sloth, Noah-OWP, CFE-S      | CSV     | 01          | No      | 3        | 1 month  |       |
| memcheck_ex_02.json | Sloth, Noah-OWP, PET, CFE-S | CSV     | 01          | No      | 3        | 1 month  |       |
| memcheck_ex_03.json | PET, Snow17, Sac-SMA        | NetCDF  | 02          | Yes     | 5        | 1 month  |       |
| memcheck_ex_03.json | Sloth, PET, Noah-OWP, CFE-S | NetCDF  | 02          | Yes     | 5        | 1 month  |       |

## Module Usage Summary

| Module                   | Utilizing Files                                               |
|--------------------------|---------------------------------------------------------------|
| **CFE-S**                | memcheck_ex_01.json, memcheck_ex_02.json, memcheck_ex_04.json |
| **CFE-X**                |                                                               |
| **LGAR**                 |                                                               |
| **LSTM**                 |                                                               |
| **Noah-OWP**             | memcheck_ex_01.json, memcheck_ex_02.json, memcheck_ex_04.json |
| **PET**                  | memcheck_ex_02.json, memcheck_ex_03.json, memcheck_ex_04.json |
| **Sac-SMA**              | memcheck_ex_03.json                                           |
| **Sloth**                | memcheck_ex_01.json, memcheck_ex_02.json, memcheck_ex_04.json |
| **Snow-17**              | memcheck_ex_03.json                                           |
| **SoilFreezeThaw**       |                                                               |
| **SoilMoistureProfiles** |                                                               |
| **TopModel**             |                                                               |
| **UEB**                  |                                                               |


