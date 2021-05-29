scheme = '[a-zA-Z][a-zA-Z0-9+\\-.]*'
port = '[0-9]*'
pct_encoded = '%[0-9A-Fa-f][0-9A-Fa-f]'
sub_delims = "[!$&'()*+,;=]"
iprivate = '[\\ue000-\\uf8ff\\uf0000-\\uffffd\\u100000-\\u10fffd]'
ucschar = (
    '[\\xa0-\\ud7ff\\uf900-\\ufdcf\\ufdf0-\\uffef\\u10000-\\u1fffd' +
    '\\u20000-\\u2fffd\\u30000-\\u3fffd\\u40000-\\u4fffd' +
    '\\u50000-\\u5fffd\\u60000-\\u6fffd\\u70000-\\u7fffd' +
    '\\u80000-\\u8fffd\\u90000-\\u9fffd\\ua0000-\\uafffd' +
    '\\ub0000-\\ubfffd\\uc0000-\\ucfffd\\ud0000-\\udfffd' +
    '\\ue1000-\\uefffd]'
)
unreserved = '[a-zA-Z0-9\\-._~]'
h16 = '[0-9A-Fa-f]{1,4}'
dec_octet = '([0-9]|[1-9][0-9]|1[0-9]{2,2}|2[0-4][0-9]|25[0-5])'
gen_delims = '[:/?#\\[\\]@]'
reserved = f'({gen_delims}|{sub_delims})'
ipv4address = f'{dec_octet}\\.{dec_octet}\\.{dec_octet}\\.{dec_octet}'
ipvfuture = f'(?i:v)[0-9A-Fa-f]{{1,}}\\.({unreserved}|{sub_delims}|:){{1,}}'
iunreserved = f'([a-zA-Z0-9\\-._~]|{ucschar})'
ls32 = f'({h16}:{h16}|{ipv4address})'
iuserinfo = f'({iunreserved}|{pct_encoded}|{sub_delims}|:)*'
ireg_name = f'({iunreserved}|{pct_encoded}|{sub_delims})*'
isegment_nz_nc = f'({iunreserved}|{pct_encoded}|{sub_delims}|@){{1,}}'
ipchar = f'({iunreserved}|{pct_encoded}|{sub_delims}|[:@])'
ipv6address = (
    f'(({h16}:){{6,6}}{ls32}|::({h16}:){{5,5}}{ls32}|({h16})?::({h16}' +
    f':){{4,4}}{ls32}|(({h16}:)?{h16})?::({h16}:){{3,3}}{ls32}|(({h16}' +
    f':){{2}}{h16})?::({h16}:){{2,2}}{ls32}|(({h16}:){{3}}{h16})?::{h16}:' +
    f'{ls32}|(({h16}:){{4}}{h16})?::{ls32}|(({h16}:){{5}}{h16})?::{h16}|' +
    f'(({h16}:){{6}}{h16})?::)'
)
iquery = f'({ipchar}|{iprivate}|[/?])*'
ifragment = f'({ipchar}|[/?])*'
ipath_empty = f'({ipchar}){{0,0}}'
isegment = f'({ipchar})*'
isegment_nz = f'({ipchar}){{1,}}'
ip_literal = f'\\[({ipv6address}|{ipvfuture})\\]'
ipath_absolute = f'/({isegment_nz}(/{isegment})*)?'
ipath_rootless = f'{isegment_nz}(/{isegment})*'
ipath_abempty = f'(/{isegment})*'
ipath_noscheme = f'{isegment_nz_nc}(/{isegment})*'
ihost = f'({ip_literal}|{ipv4address}|{ireg_name})'
ipath = (
    f'({ipath_abempty}|{ipath_absolute}|{ipath_noscheme}|' +
    f'{ipath_rootless}|{ipath_empty})'
)
iauthority = f'({iuserinfo}@)?{ihost}(:{port})?'
ihier_part = (
    f'(//{iauthority}{ipath_abempty}|{ipath_absolute}|' +
    f'{ipath_rootless}|{ipath_empty})'
)
irelative_part = (
    f'(//{iauthority}{ipath_abempty}|{ipath_absolute}|' +
    f'{ipath_noscheme}|{ipath_empty})'
)
irelative_ref = f'{irelative_part}(\\?{iquery})?(\\#{ifragment})?'
iri = f'{scheme}:{ihier_part}(\\?{iquery})?(\\#{ifragment})?'
absolute_iri = f'{scheme}:{ihier_part}(\\?{iquery})?'
iri_reference = f'({iri}|{irelative_ref})'
