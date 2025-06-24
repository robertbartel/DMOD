import argparse

from datetime import datetime
from pathlib import Path
from string import Template


ARG_DATETIME_FMT = "%Y-%m-%d,%H:%M"

PARAMS_TEMPLATE_STR = """hru_id $cat_id
hru_area 8.845200310497782
latitude 41.826039941401916
elev 18812.947221297498
scf 1.100
mfmax 1.21585524082184
mfmin 0.295154213905334
uadj 0.0348296314477921
si 500.00
pxtemp 1.000
nmf 0.150
tipm 0.100
mbase 0.000
plwhc 0.030
daygm 0.000
adc1 0.050
adc2 0.100
adc3 0.200
adc4 0.300
adc5 0.400
adc6 0.500
adc7 0.600
adc8 0.700
adc9 0.800
adc10 0.900
adc11 1.000
"""


def _parse_args() -> argparse.Namespace:
    """
    Set up and run top-level arg parsing for module.

    Returns
    -------
    argparse.Namespace
        The parsed arguments namespace object.
    """

    def parse_dates(date_string: str) -> datetime:
        formats = ["%Y-%m-%d,%H:%M:%S", "%Y-%m-%d,%H:%M", "%Y-%m-%d,%H", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                   "%Y%m%d%H%M%S", "%Y%m%d%H%M", "%Y%m%d%H"]
        for f in formats:
            try:
                return datetime.strptime(date_string, f)
            except:
                pass
        raise RuntimeError(f"No available date parsing patterns matched ({' | '.join(formats)})")


    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, prog='gen_snow17_init',
                                     description="Generate naive (but computationally valid) BMI config for Snow17.")

    parser.add_argument("--template", dest="template_file", type=Path,
                        default="/dmod/qa/bmi_configs/snow17_init_template.txt",
                        help="Specify path to template file.")

    parser.add_argument("--param-file", dest="param_file", type=Path, default=None,
                        help="Set path to Snow17 param file (if not set will be based on output file directory).")

    parser.add_argument("--output-dir", dest="output_dir", type= Path,
                        default="/dmod/qa/ngen_ex_bmi_cfgs/fortran",
                        help="Specify parent directory for generated file.")

    parser.add_argument("--forcing-dir", dest="forcing_dir", type=Path,
                        default="/dmod/datasets/forcing/test_forcing_01", help="Specify forcings directory.")

    parser.add_argument("--forcing-filename", dest="forcing_filename", type=Template, default="$cat_id.csv",
                        help="Specify the name or name pattern template string (using '$cat_id') for the forcing file.")

    parser.add_argument("--start", dest="start", type=parse_dates, default="2015-12-01 00:00:00",
                        help="Specify start value for 'start_datehr'.")

    parser.add_argument("--end", dest="end", type=parse_dates, default="2015-12-30 00:00:00",
                        help="Specify end value for 'end_datehr'.")

    #parser.add_argument("--group-id", "-gid", dest="group_id", default=1000, help="Specify host user id for owning created files.")
    parser.add_argument("cat_id", help="Specify catchment id.")

    return parser.parse_args()


def gen_init(template_file: Path, output_file: Path, cat_id: str, param_file: Path, forcing_root: Path, start: datetime,
             end: datetime):
    template = Template(template_file.read_text())

    # TODO: (later) sanity checks on paths and dates perhaps
    datetime_pattern = "%Y%m%d%H"
    values = dict(cat_id=cat_id, param_file=str(param_file), forcing_root=str(forcing_root),
                  start_datehr=start.strftime(datetime_pattern), end_datehr=end.strftime(datetime_pattern))
    output_file.write_text(template.substitute(values) + "\n")


# TODO: perhaps in future, more intelligently examine hydrofabric (although maybe that belongs elsewhere)
def gen_params(cat_id: str, output_params_file: Path):
    template = Template(PARAMS_TEMPLATE_STR)
    values = dict(cat_id=cat_id)
    output_params_file.write_text(template.substitute(values) + "\n")


def main():
    args = _parse_args()

    output_file: Path = args.output_dir.joinpath(f"snow17-init-{args.cat_id}.namelist.input")

    # Param file will always be with a standard name based on catchment and in the same dir as the output file
    param_file: Path = args.param_file if args.param_file else output_file.parent.joinpath(f"snow17_params.{args.cat_id}.txt")

    # Not sure what else to possibly put in here
    values = dict(cat_id=args.cat_id)
    forcing_file_name = args.forcing_filename.substitute(values)

    gen_init(template_file=args.template_file, output_file=output_file, cat_id=args.cat_id, param_file=param_file,
             forcing_root=args.forcing_dir.joinpath(forcing_file_name), start=args.start, end=args.end)

    gen_params(cat_id=args.cat_id, output_params_file=param_file)


if __name__ == '__main__':
    main()