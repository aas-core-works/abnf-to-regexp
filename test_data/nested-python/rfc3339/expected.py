date_fullyear = '[0-9]{4,4}'
date_month = '[0-9]{2,2}'
date_mday = '[0-9]{2,2}'
time_hour = '[0-9]{2,2}'
time_minute = '[0-9]{2,2}'
time_second = '[0-9]{2,2}'
time_secfrac = '\\.[0-9]{1,}'
partial_time = f'{time_hour}:{time_minute}:{time_second}({time_secfrac})?'
time_numoffset = f'[+\\-]{time_hour}:{time_minute}'
full_date = f'{date_fullyear}\\-{date_month}\\-{date_mday}'
time_offset = f'([zZ]|{time_numoffset})'
full_time = f'{partial_time}{time_offset}'
date_time = f'{full_date}[tT]{full_time}'
