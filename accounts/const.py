TEXT_UPDATES_NEVER = 0
TEXT_UPDATES_ALWAYS = 1
TEXT_UPDATES_SOMETIMES = 2
TEXT_UPDATES_MAYBE = 3

TEXT_UPDATE_CHOICES = (
    (TEXT_UPDATES_ALWAYS, 'Yes, every time'),
    (TEXT_UPDATES_SOMETIMES, 'Yes, on some trips'),
    (TEXT_UPDATES_MAYBE, 'Not sure'),
    (TEXT_UPDATES_NEVER, 'No'),
)

APARTMENT = 'AP'
ASSISTED_LIVING = 'AL'
RETIREMENT_COMMUNITY = 'RT'
SINGLE_FAMILY_HOME = 'SF'
SKILLED_NURSING = 'SN'

RESIDENCE_TYPE_CHOICES = (
    (None, ''),
    (APARTMENT, 'Apartment'),
    (ASSISTED_LIVING, 'Assisted Living Facility'),
    (RETIREMENT_COMMUNITY, 'Retirement Community'),
    (SINGLE_FAMILY_HOME, 'Single Family Home'),
    (SKILLED_NURSING, 'Skilled Nursing Facility'),
)

HOME_PHONE = 'h'
MOBILE_PHONE = 'm'

PREFERRED_PHONE_CHOICES = (
    (HOME_PHONE, 'Home'),
    (MOBILE_PHONE, 'Mobile'),
)

UBER = 'Uber'
LYFT = 'Lyft'
UBERX = 'UberX'
UBERXL = 'UberXL'
UBERASSIST = 'UberASSIST'
OTHER = 'Other'

PREFERRED_SERVICE_CHOICES = (
    (LYFT, 'Lyft'),
    (UBERX, 'UberX'),
    (UBERXL, 'UberXL'),
    (UBERASSIST, 'UberASSIST'),
    (OTHER, 'Other')
)
