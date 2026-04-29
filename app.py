import streamlit as st
import streamlit.components.v1
from login import render_login_page, render_admin_panel, render_wachtwoord_reset, render_landing_page, render_disclaimer, get_abonnement, render_abonnement_keuze
from mollie_payments import render_credits_kopen, controleer_betaling_url
from carboo_coach import render_coach
try:
    from module_testing import render_testing
except ImportError:
    def render_testing(user): st.info("Module nog niet beschikbaar.")
try:
    from carboo_coaching import render_coach_dashboard, render_coach_uitnodigingen
except ImportError:
    def render_coach_dashboard(u): st.info('Coach module niet beschikbaar.')
    def render_coach_uitnodigingen(u): pass
try:
    from fuelc import render_fuelc
except Exception as _fuelc_err:
    _msg = str(_fuelc_err)
    def render_fuelc(user, msg=_msg): st.error(f"FuelC: {msg}")
try:
    from carbomax import render_carbomax
except ImportError:
    def render_carbomax(): st.info("Module niet beschikbaar.")
try:
    from raceprep import render_raceprep
except ImportError:
    def render_raceprep(): st.info("Module niet beschikbaar.")
try:
    from optimeal import render_optimeal
except ImportError:
    def render_optimeal(): st.info("Module niet beschikbaar.")
CARBOO_AVATAR = ""

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
_favicon = "🏃"

st.set_page_config(
    page_title="Carboo — Sports Nutrition",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── GLOBAL STYLES ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0a0f1e; color: #f8fafc; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
.stApp { background: #0a0f1e; }
.block-container { padding-top: 1.5rem; max-width: 1200px; }

/* Brand */
.brand-header { text-align:center; padding:20px 0 10px 0; font-size:2.2rem; font-weight:900; letter-spacing:4px; }
.brand-header span { color: #f97316; }

/* Buttons */
.stButton > button { background:#f97316; color:white; border:none; border-radius:10px; font-weight:800; font-size:1rem; padding:14px; width:100%; }
.stButton > button:hover { background:#ea6c0a; border:none; color:white; }
.stButton > button[kind="secondary"] { background:#1e293b; color:#f8fafc; border:1px solid #334155; }
.stButton > button[kind="secondary"]:hover { background:#334155; border:1px solid #475569; }

/* Inputs */
.stNumberInput input, .stTextInput input, .stSelectbox > div > div, .stTimeInput input {
    background: #0f172a !important; color: white !important; border: 1px solid #334155 !important; border-radius: 8px !important;
}
label { color: #94a3b8 !important; font-size: 0.78rem !important; text-transform: uppercase; font-weight: 700 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:#0a0f1e; gap:8px; }
.stTabs [data-baseweb="tab"] { background:#1e293b; color:#94a3b8; border-radius:8px 8px 0 0; font-weight:700; border:none; padding:10px 30px; }
.stTabs [aria-selected="true"] { background:#f97316 !important; color:white !important; }

/* Meal cards */
.meal-card { background:#0f172a; border:1px solid #334155; border-radius:12px; padding:18px; margin-bottom:12px; }
.meal-card-title { color:#f97316; font-weight:800; font-size:0.85rem; text-transform:uppercase; margin-bottom:10px; border-bottom:1px solid #1e293b; padding-bottom:6px; }
.section-title { font-size:1.4rem; font-weight:800; color:#f97316; border-bottom:2px solid #334155; padding-bottom:8px; margin-bottom:20px; }

/* Results */
.result-ok { background:#f0fdf4; border-left:5px solid #22c55e; border-radius:8px; padding:14px; margin-bottom:10px; color:#1e293b; }
.result-low { background:#fef2f2; border-left:5px solid #ef4444; border-radius:8px; padding:14px; margin-bottom:10px; color:#1e293b; }
.boost-tip { background:#fee2e2; border-radius:6px; padding:8px 12px; font-size:0.8rem; color:#991b1b; margin-top:6px; }
.metric-box { background:#1e293b; border:1px solid #334155; border-radius:12px; padding:18px; text-align:center; margin-bottom:10px; }

/* Timeline */
.timeline-block { background:#f8fafc; border:1px solid #e2e8f0; border-radius:14px; padding:16px; margin-bottom:14px; color:#1e293b; }
.timeline-uur { font-weight:900; font-size:0.95rem; border-bottom:2px solid #3b82f6; padding-bottom:5px; margin-bottom:10px; display:flex; justify-content:space-between; }
.timeline-row { font-size:0.85rem; margin-bottom:6px; display:flex; gap:10px; }
.min-label { color:#3b82f6; font-weight:700; min-width:45px; }

/* Alerts */
.alert-orange { background:#fff7ed; border-left:5px solid #f97316; padding:12px 16px; border-radius:8px; color:#9a3412; font-size:0.85rem; margin-bottom:12px; }
.alert-red { background:#fef2f2; border-left:5px solid #ef4444; padding:12px 16px; border-radius:8px; color:#991b1b; font-size:0.85rem; margin-bottom:12px; }

/* Selectbox dropdown */
div[data-baseweb="select"] > div { background:#0f172a !important; border-color:#334155 !important; color:white !important; }
</style>
""", unsafe_allow_html=True)

# ─── PWA meta tags ──────────────────────────────────────────────────────────
_ICO = "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAIAAAB7GkOtAAA5AUlEQVR42u3dd5wURcL/8arumWUDuywZlixxyTkpIoIEBURFPFFU7rw78xnwznSPpz/TnQGz53lglsOEEUVAQBSQIEFyjrsgaReWTdNd9fsDFNgddmdqZ2Zndj/v1/PHcyvT09VTXd/u6uoqWXBXHQEAqHwsDgEAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAACAAAAAEAAKgkPDG517ZX1kuXDdrL6g1lappIbSBT6osqidITL+IShDdeKFc4BcJXoHMPiaP79dH9+sA2fWCL3rtBZ64Vro8fHiiVTE2TjbrI2s1lagNRvaFMbSDik6U3QXjjT5xlvjztyxO+fJFzQB/eow/v0od368y1evcq4cujyDFQ3oK76sRIVMVZLc6R6YOsxt1kWjthew234xTqjNVqywK9ca7a9qNwCjnPgVNbQKvdUNl6gGzURSbXNtyKcvW+DXr7UrV2htr0XZSfZZWwyLETAJbHajfE6jbaanWeiEsM8cYLc9XamWrlp2rdLOEURKxM3tu/kQ07mX9eub5HuuojeyNRP9Lae++cHeKNai2UI5xC4fp0/hGRe1jnZonsDH1opz60U2eu0/s2RuYuLSylU65QjnB9winU+UdEXrbOyxbZe3VWhs7eo/dt0nvXidysqDvRElLtXmOtzqPKVDP9KjimNnyrFr+nNswRWlNkAiCwPUuuY/W5xup1taxWP+xflpflLpmqFr6l928Oe7nqtvLePb+MG3G/eNid+1KsNpGlF8+n96xWG+epDXP09sVCqwpVOiF0dobe+qPaulCvm6Wz9pTziVa3pd3vz1a30cKbEN5S79+svp/sLn6v3LtKKmGRYyoA4pPt826x+/853D9P8StTtfYbd/azeudP4fsS+6K/2wNuKeue7t3ge+rcChsAp7WVmeqnj9SC1/Xh3RWvdEIIvfMntexDd8kUUZgb6ZO/ai176D1Wz7HCsiMZfu70x9RPH5bLpXElLHJMBYCUVp9rPUP+JpJqlONeOP+9Uq3/NjwFtLx/Xy5T6pV9S75nB+vdKyt8APzar+KoZR+6Xz+hszMrYOmEEHnZ7vzX3DkvRuhSUUq735/sIX8VVaqWT+ztWuF8cKfOWBPJtqXSFTkAUTQMVFZL8/zpfc+l/yzf1l8IITxVwnW4W/UPSesvhLC6jxGVh+WxevzOe/d8q881FbOACdXswRO8f1tgtewX9hMtuY7nj1PtkQ+XV1MohJCNOntv+9o+548R+rrKV+QYCwCr43DvhLlWy3NFhWZ1vyJUm7K7XGo+FCpGxSd7LnvSM2ZiRS24TE3z/HGqfd5NYayBzft675prtepf/qX1xNmjHvH8/m1RJSm8J13lK3KMBYA94BbPuP+KhGoVvv2y2g8L2daSalhtBorKx+o51nPVK0JW0HcYLdse/qA96I4wXWZ5/jhVVK0ZRcVtO9h7w8fh26VKWOSYCgDL9lz+tH3R34WUFb/l6jhCeONDucEeV4hKyeo4wh7+YAUuoD30HqvjiBAftN7jPONeE564qLvvadTZe/PnMrVB6OtJ5StyTAWAlJ7Ln7F6XV1Jmi071O21lX6BSKxeOTPAPvfPFbvD0DNmYqgeFwkhrE4Xey57Mmpvm2Tt5p4/ThUJqaE8OypfkWMsAOyRD1s9fldJGixZs4ls2ivUR9Brd7m0cgaAkNK+9PFIDuaLtPhke+jfQnOozurjufLFKL/JlnVbese/Eaqr9UpY5BgLAPu8m+1+f6pEvRbdxoSjOlausUBFr6FaWF0vq8h1pvsVZX8LUqamlXsrE0Srfdm/QrCdyldk8xvN8il2s172hfeFams6O1NvXaS3L9EHtuqDO3TuIVGYK5Qr4hKlN0Ek15HVG8paTWXDzrJRZ1mrWTkFwOVhOZKNOsu6LfW+TZUzA+ze16il71fcBLCtHle4s54tQ/2w7CtfCkE/g1Z6x1K1Ya7evUrv36yPHRIFx4TtkVWqiuoNZZ0W1ll9ZZsBslpaWUvc40pr3Sy16guKXHEDILG65+p/C6vMX+0UqCVT3WUf6B1L/L9il39U5x8VR3/RGatPuTpoINsOttoPs1r2i1j/oGzWW9ZsEr7rRPfLRyrpTUDTHrJGY31oZyS/VB/c7nu8xN48b4JMqCbrtJBNulndx8jaLcx/3HbDyhIAdv8breZ9y3iWud9PUgsm60O7iv4n5ejjk2LuWqGWfSikZbUeYA24pYzf6Bn9lG/7En1kH0WumAHgufSJssamVu6CN9SsifroL0F/NGuPXvC6WvC6rN7Q6nmV3fe6CLx3ZodzuI7VdbQ7/bHwTZgTyiZSWqJKkoxLEtXqyXrpVuOuVqcRZXyOLVv20z++G1255MvTvjx9ZK/Y/L07+zmr+xjPqEdFfIpJ6Rp0EPEpIv+IUU9IgzI+RVDrv3U/nBDobEVaqfWz1frZVvsLPaOfMh/mmFjdHvmw886fKXIkbjIjfcl2Vh+r86gyNS4HtvleuMiddq9B63/adg7vdmf8s/DRbu4XD+mj+8NYZm98yIf0nXZIq9WPmfEwWon8o/rIXr1rhVoyxfno7sKHOjgfThB52eY1uFmvKC+0Wvq+7z9jDKf6sWxZP93wsmPYfWV5p92d8U9n0liDuerU6um+ZwboncvNf9NOF8tGnSlyhQsAy/aMerRM59LGub7nhoZysrbCXHfuy74nertzXw7TFMRW+wtFfHJ4j2vsPgp2fWrR275nBxtnsKzbOgaCb+dy95snDQto9NRKNuhQlifk7rT73JnPGE9epo/s8706Wm/70fSiRhq851EJixxjAWB1uVSmtTNv/dfOdCZdLfKyQr9nBTnuFw/5nuqvty8u/9ZZ62BnpbY6XFiOk5yEpMvIfcdwSFj4Hq6EOOm+nyQKjpkUMLmuybXwwNuNR525c150f5hU9nPK9/o1+uB2w7OmeV/ZtCdFrlABYPe/wbyN2Paj8+b4sK4Tovdv8b10sfv5P4QvP2T9Myn1gu2f0dt/VN8HWRe9CVankSKWqS0L1CajZRISq8fG2wBOgdq60OSDwc8bI1PqWe2Hmp5oi9zpj4amyLlZzpu/Nz5n7bN/T5ErTgBYLc6Rae1Nb6/2Om9dH4lVorRy572iNswJWam7jQ62eXKXT1MrPxPKDa7qxP4LAWrV54afjPC6EeY3OtuMWoWgZ76z+lxjOMrOKXCm3hHCAQU6Y4377QuG507H4YEv0FgJixxrAXDOH8xvnz+YUMZHvuXF6hZku6wctepznXNAbf4+uIu+Zr1ljcYxHQB62yLDT8bCKz9CCJFnMphHFOQEXet6XGl4ov0wWR/YGtpCu98+b3jy2l6r62iKXCECoEqS8dSVatUXat3MWGzRZKPOsl5wjyjVxu9EzkEhhFrxSZBfJsP0rlnkAiArw/CT+Udjo4QJJiNBgx0iJRt0lKlGw6x9ee63z4e+1L48Ndtws1a7IRS5IgSAlT7IcHiWVu7XT8Roi2bQIqsV0078Pz9/GWyXV8xPC5F/VCgn+JMtPzIryIfggqBGU5MzYP+WyLQgavk0cexQOAruLv2f2ShY2bSnSEylyLEfAB2GG1/+619ic54Dg5nanAK1+qvfrvuCXZZS1mwqo35QfMk3MUIEPYpDh2NUWHjqg9W8j8kpsGdVcOda2wsM26zwvU+Xf1St/NSo4bAD6TmohEWOtQBocY5hAPz4Tqxe/qcPCvYdY7V25qm9Gb/dDQTRyHSP5RUC4lMMxvPovRtio/3ve53BUF2dseZ4l2CgvAlmQy30kX1657LwFV/9PN3wPCp1ZGQlLHJsBYCs1cxsugWdnWk4NDAaAiD4trhIv79aMyPYJcKtTiNDu+ZMRG8AqjcyqSS7VsRA0dLa20NMpihQyz4I7osadDAbFKvXzTJ+Byqggmz6TjgFJoeutPdjK2GRYy0AmnQz+6BePzuqprgJQmJ1K31QcB8pyCn6rLswV635JsiL6GSr3VARm6yzTHpIQvlaeJjK1XmU94aPTN4Gzz/iLp0a3Hc16mTYWhkPwQqQL1/vXmnSetRvW/JA2EpY5FgLgIaGgaY2zovRtsxgxXa1+qviL6AZ9AJZMdsLZHUZZdBEqo1zo64k3niZUlc272uff5t3wneeq181e6znzn4+2EeUxm/a6x3Lwn1U1PalJh/zxMk6LSlymERiNlBZq6nhL2R2+KKhLQt+QI5a7qetV+tni/wjQU0kabXqL1PqlsvUsmU6Ym0GyibdTQ5a6F7bDrQ+12wa91TYD6/evsT97t9Bf6y60bsgToE+sC3sJdq73vCAV2+oM9dS5Ji9AzDq2xV5WTo7Q8QgWbdV0L14uYf93+44hUE/SrLsCL9LEoIjVqelZ+zLwZ9eyl34pqiIdFaG89YfDIa3mg2H1we2R6Cv1fx9qxIXT6+ERY65AGhocuz2bYzZy//gH/+u/OxMQ+D93hmEfAfKje21+l7n/cvXBp0katE7OmNNBWz99210XrzI7B7OsDWMzIo6B3cYNiAlFqoSFjmEwt8FFJ9sNlGlzs6MydNXWgZz0rpnfu9XbZ4vcg4GtdaErNdaNuiogxw/HpGDI0VcoqxSVaTUk/XbWk26WR1HmPWP65wDTqgm8IomavF7zmcPmq0AIxJTDV+3zNkfgaLpY4eE1gYTdsqUuhQ5VgNAmk5THHO92CeuvlueG+xC3sfXND5zk+CqVZ9ZfccHtxs9xrjlFwBh7yX35TtvjBex8gpYgE3/5u/dmU/rLQvMD7s30bSdOhiREjoiP9tktd64RIocrvYq7N9gPFOj2cxZ5R4APQyG/39acneku/yToHtWulwWsZFkEW8pXeedP4dj5YZypLcudKc/UpbWXwgh4kzPNbPVygyKWWD0RSW82lIJixxrAWBaEqN3KMpZfLLV/sLgA6CUXn69/cegn4cn1YjkC+WRk3vY+e9YtebrClYseVYf721fe++ebwU7fUhozrXCCJXT7KQu4TK/EhY5xgLAeKreGAwAq+OIYGukPrCt9HdZtVYrgp5XxOoRy9NC+D0MO5b5nhkYjQP/QxUDdVt5rnrFe8sXhitnGJ9rEZtNz3VMDksJ5aqERY6xADA+0HZczJ3AtkH/T2CDfIKeHVoIK/0CkVi9gjT9h3c7U272vXiRwYLdsRcDTXt4b/3S6nRx5K5qI9ZbaJs8dNQllKsSFjnGAqAwz/CDsTanjazRWDYNejLOAN/11btWBD2m2PbaXS6J+aZ/1wrno7t9/+yjln0Y1plboos33nP1q3b/G4P7lPE7cRFrDc1G7JQwI1YlLHKMBYBxSQzmTilXVvcxwY730plrA3/dwaQXKKYnBy3MdT6c4Ht+mFr4VuR6bKPogkLawx+0Og6PxLkWqTEn0uyLSgqAylfk2AoAbfq0XabUi7EA6Baa6R/O/I8/DvoYNuos67YUMSou0TP6Ke/9S62+42Nm0cdQZ4DnyhdlvTZhP9eq1orIGWKLhGqh7UWohEUO8f1J2L8hL1sU5hrkrawWSwEgm/WWNZsEHQDBzPWm923Umetk/fRgbwLcLx+J4TYwtYHn0id03+uc927WGaujYZf0we2+x0vs65OWiE+WVaqKGo2thh1li3OsNucbLlnuTfBc+oTv5VGBnmtOoUlYJtWMxE+ZVMPglSghhD66jyLH6h2AEEIf3m1y7Oq2iqF2yuDxr96xVB/aFb7AOPEDdx0tpCVinKzXxnvbV8H1h5RnRCiRl62z9uitC93vXnUmj/M90lUteMPsGYY8q4/VaWRg36vN3p+XNRpH4rAYf0sJi0VXwiLHXgCYTbuRWD3YV2rLjTfe6jgi6Mv/4Cf5MRgLJKvVt1r2qwj9IZ44z7jXYnThe31kn/Px35xJV5k9zLAH/iXQLzIaJSVrNTO7UA3uW2o3Nzx6JRaqEhY51gLg4HbDw2e6kkyEWe2HBf3IWrlq5WfBH8kdeufyoHeve0V5IUBanjETYzfP1PrZzv9uMSl3WvtAZ70/vMtkz7zxsmbTsP96dVuHpQuhEhY5xgLAaFkcIYTV6rzYCACD6T+3LNBHfzFpRIJ/FGx1uFCYzsgUdWyv55r/ymppMbr7asWnatN3JnUssFsf4+lRDRZjCLoITY2+wvWVPFKuEhY5lPfVkQgA05V3ZPpAIWWUj/6WKfWslucGXTNa9ovAoiK/XuwkWJ1GqsXvRa7Ho/hjUk8VmZAiUhvItHZW+iCrzSDzgT0JqfaVLzqvjo7R5ULVty+YVJiz+riBbHzXSttor6yzege7/nCQLU0Vs5UBdebakl8mrYRFjrU7gP1bRG6WSdtaLc1qcU60X/53G222JnVEr5vLvevcKdBH9+tdK9SP7zpvjC98pLNa+JZxC261ONsOcnrUKAqAbYsMRnkHuE6s3rPK7KjK9EFh7RO3Wp5r9mqn3rWSIsd2AAgh1ObvDfev17ioD4AxIurJs/pEaNhDgHIOOh/d7bx1vfGbnPaweyI0lDv0WVioM4Jf7c8TF9C4uMJcsy4RmVJPNuoSxtOkw4WGTUep075WwiLHXgD8/IXh/nUaYfwkPRINa8NOsl5rEf2kjMLxM+rnL503xwvlmnw4PsUe/n8xehOgg1zq/cRvmFwnoKO6dqZhpva6OlwFrlLVZGojIYRy1frZFDn2A2DtTMO3+aVlD/1b9F7+d4+By/9o3lW1/lv383+Y3ntdHvhbstGl4KjJpxJSAjvXZhgezy6XmK3OVno72+N3okqSSVLuWCoCCMtKWOQYCwBRkGMca1ani60250fjaWx77bLM3h7he4CaTWWzXlG4Y+73rxn2EErLHnZvTAZAfEr4PqV3rzRcTjUu0R5wa+gL6423zjfcrFozgyJXiAAQQv0w2bylvfzpKOzwtdIHiaQaMdTs2NF5v6K1+/4dZg8DrHZDZaPOMdf+G1bmAPvKtFZL/mdYQ865PuSj4+0BtxjO6+X6Ah2lUwmLHHsBsOk7nbnW8ISpluYZ91okZnCVlt3/Bqv1gICOXez0//x6LzXScHLacEfAoZ3u968ZnmxD/hpjzb83IdC3uooIeOIztfAtwycr3njPmIkhHBsj66fbA283bDF+nh74uzKVsMgxFgBCCHfev80Pa/O+4c4AWbu596ZP7BEPBTR4K7G6lX5BzPU8WO2HReeuubOfF7mHTWpwm4GycddYiuGW5xhW47zsQAM1O8O4W1w272sPDVHHWkI1z7WTjc9ZN5g+g0pY5NgLAPXThzpznfm+th/mGf+mYf9pyapUtYf/n3fCvMB7ye0ul8biquvROy1E/hF3zkuGNwGD746hn8C40zmoKVXcWc8av0FpD/yL1efaMp9TSd7r3pC1zjIs7LZFetui4FrPylfkGAsAoVz3k/vKtLttBnr/8nUou33jEu3+N3rvWWSfd3NQDXrM9f+c2O1W/WVK3Si9Cfhhktn4B6vN+TEzbVTPsYaP4l1fUHPH6t0rDeaO/Y3nsn/Z5//FuGNEJtfx/ukD2byv8Q44nz8UdANa+YocawEghNqyQK38tCxbkLWbe2/7yh71qEyuXabtVG9oD/lr3P3L7BH/CHZTsm7LWHz2KIQQlm11vSxK960w1537cgW+CbA6XOQZ/aTh5eHOn4QKbnlx96vHyrKSmn3hfZ7fv20w7ZLVbojnzm/LEslq5Wd6508mKVn5ihxjASCEcD6+x3DM1skG2LLPud57/zLPZf8KdkYnmZpm9b3O86ep3vuW2BfcZTaMJ6bn14zmnTe/CWg9IJpvAmRqmmfMRM+1kw2XhRFCbf4h6Mw4tMv95skyVZX0C7z3LLQv+rus3jCAQkqr9QDPDR95xr9Vpouz3Cz3M8NX/CphkcvIUw7feeyQ884N3hs/LusUOp4qVp9rrT7X6qwMvXWh3rFU79+iD+7QuVmi8JjQSngTZFyCSK4jqzeUtZrJhp1ko87GPXSnxo/VdXTQVTMrw/do15BPbGePeMjuf0Nwu1+vjWzQUe9ZFbU3AfZFD5gciiF/df4THdkmLVGlqoxPFjWbWA07yhb9rDbnl3FZHrPODXfOi1b6QNmst/kXe+PtAbfY592kty9WG+bq3av0/i362CFReExYHlElSaY2lHVbWmf1kW3Ol6kNQnCB+NHdZblArIRFjrUAEEJvW+R+9bjZee738kp2vUxEqmfDanmuwUo1auWn4ZjWVK38JNgAEEJYPca40RkAQrg/TLLPu8ngzsxqdZ5s0l3vWBr25r1m08jN5Hr8fNmxzHB+YK2c92723vmt4cq0p0SabNbbLkurGmB9XjrVYJ2Myl7k2OoC+jWoX3DnvyZikNXD5DLTYDGvgGr7zuUGC67ZXS6L3iFMZXkSEHPvBAR4ssx82ryGHN7tvDk+YtMLl6kyb1/sfBiCZzmVsMixFwBCCPezv6ulU2PsXKxS1Wof9CR/+uB2vWtFuK4gDB6qJ9WI0tk1fr0JMHwS0Kq/bNqjgrX+atP8Ms4Opjb/4Pzv1ihfV0Pv3+ybPE44BaE5aJWvyLEXAEJr5/071I/vxNLlf6eRBnN8qxWfhrGBWGFy/xjVz7G5CfhNXrY79bYQVJLl05xp90btEjr6wDbntd+ZrRpCkWM2AIQQynU+uMud/miUZ/XJ9sVo+H9ZhieXXpP2rNIHtgb9w7cdLBKrR+9NwILJhjcBLc+VTXtWkNbf9Tnv3qizMkJzqi143Xn3hijsGNF7VjkvDg/qLQeKXFEC4Hg9//Z55+0/ivwjUX4+yhqNDUYX6H2byvL+c7huAmyv3eWS6D3WBcfcea9U6psA5ThTbg7t1PBqxafOf680m3IjXKVcP9v38iU650DYTo1KV+TYCwAhhFr1ue+p/mrT/Gg+Ja3uYwxeFAzr5f+Jr1j5iVFxovptBvMnAS37RefE10HIzXL+MyYcPYdq03zf0wOMV+gL7f2N+/k/nElXiYKc8J4dla/IsRcAQgidleH853Ln43vKP67P8FjGbFGtMI3/Oe3QZa7T+zYFfUPTqLOs25KbgKi79F8zw/f0eQZvfgVaW7IznVcvd794SBQcK78+kJ99zw9z570Smb7fSljk2AsAIYTQWi14vfCxnu63zxmvFlumb1/7je/5YWr9t36ay2a9DOYN13t+1vu3RKLVMJpgI8oXNDa/CWhxjgz/CO7QV8BdK5xJVzuvXxP214K0cue+7Huit1r8XoQfk+oje52pt/ueHaz3/BzZg1v5ihx7AXBc/hF3+mO+x3u63zylj+yNxDfmZbvzX/M92c+ZPO5MM3LY3c2G/38amWNm2AvU7fIyvqHKTUAI+PLV8o+dV0f7nhui1s2M2Nfqo78479/he/o8tfi9CFxv6QNb3U8f8D3eWy2ZUl6DcyphkUvpBii4q05UnxuWx2o/1Oo62mrVX8Qlhv7EWzdTrfhUrZtZSm3wxsc9+LPBTNS+x7pH7Fm/9665sn56sJ9y/jNGbZx3xvqR1t57Z9DPIfXB7b7HQ9QLXyUp7r6lZlM2+V4epbcuLKn2G5UuVBekev8WvXWRWj9bbZofvk7huCd2CU/cab/4G9ep1V8V/XeJqXbPq6wul8gGHUK8B4W5av23askUtX52dA32q4RFLsYjopxy1Kov1KovhCfOatFPpg+ymnaX9dLNX2R1fTpzrdq6SG+Yo7YuDPAqwGp/oUHrr3csi+RIL7XyEzv4ALC6X1FCAETJTYB94f0miXjTJ7/VIt+/+hkMli3b7+EK1yfcQl2YK44d1rmHxdH9+vBOfXCH/mWz3vNz9DwJFEKI3Cx37kvu3JdkagOr/TDZ6jzZuIv5OqzK1b9s0tuXqLUz1MbvyvddJ4ocy3cA/m/vvTKtnazfVtZoLFPTRGoDmVJXVEmS3gThjReeKkIr4RQKX77OPSxy9usj+/TB7Xr/Nr1vg85YHeyEsVar/vYlj8naLQKrVYedr/+pFrwuKjSr11Wey585Le2yM33/r3P5X9GMf9NqN9RfOn7qvP0n/x+57EmrzzWnlWXvBt9T51aMAxjIHcCZdkZWbygbdZa1m8vUhqJ6Q5maJuJTpDdeHP+/Yp2HavVXetN8lblW714Z+AKW0dUgllxk5Qpfnvbli8I8ceygPrxbH94tDu+O3SJ7YrL5cX1614rwTa5wWtb0+6N98SPB3FdWl7WbC0RbYnUcKRu+pHev5FAEcQt7vIELOFrU0ql+OpcqUJEr4HlBLS/l2j+o1h/Re2knQzX7LFBheDgEJV3+j/gHB6HixHnLc62W56pN31WqUhfe0yjmtgwCIAouGWs3l/XbFr1D3L/ZnfOS3rpIZ2cKt1DEJ8vkOjKtvWzS1Uq/wOBFAUQ00S96QD03JFYmngIIgPILgOIjavKyfC9cdNoEfrlZOjdL79soln/sfvKArJ9u9bpa5GX53eAZH8dZHqvLKKvDcJnWXibXFk6+PrxbrZ2lfnw7wO5IWT/dajdUNuslazeXiakiLlHkH9XHDumMNXrbYrXyU330lzN9toSHhLJhJ7vvdbJJD1m9gYhLVMs+1Ecy7QG3+t+HavWLL5PifHCn+vHdU/6RtJqfLdsNsdLai1rNZHyK8MaLghydly1yD+ujv+j9W/Xe9Xr3Sr13Q7BL4AZ0oBp2sjqONHhpzu+AUd8TvfWBbUXPqGJPodXi95z37/gtgYwPYFC/lDPl5lI/VZadEYEPMA1FLS3566x2Q6zOo2TjrjKlrlCuzspQm+ap+a/pgztoxwgAU8Umy9R715c8favOXOd+EtyARdmgo+fKF2S9Nif/5I2XCal2Wnu7/5/dLx91vy9p2RxZr4098mGrVf/iOy+PP47uNNIe8aBa9oHzxUNBzD1r2Z5LHrf6XHv6l8myHE5Zr7Xnyhdlg45F/0NCNZlQTdRoLIUQv2au89Ff1cI3w3ITMOwe9fOXoUmXaLiTCMMvFfrcDVMtFULWbuG5YmKR+V9l3VZ23VZ2n+ucDyeoJf+jJSup+nAIzij/aLFLmHYyNS2UJ0bTnt6bpp3W+p/Km2CPesQefMYFg6zuV3j/MsPPeVW0zfNaPcd675wjG3YK9Lrg8qeLtilla1Zkjcbemz/30/qHn/5l06kTAstaZ1m9rqo4V3Ch/qVC38SErZbKxl29t35xxtm/ba9nzLPRvPARARDVdOaaon+KT/b85Rt78N2ycdeQLKlon3eTqFK1lH8zeIKVPsjPL9d+mOeKZwNfnUampnmvnyJrNim9TnQdbfW4MsTX3Rc+UNY1Wo1/x8O73dNvJuzBE4Q3ISTbLuezNwy/VIj3MGy1VAhhn39bKWtaSGlf8nhUT3ZCAERvAOzbpIutnC6Ta9uDJ3hv+yrusW3eCd95rn7VHnCLbNqzSO9kiFvP0U8WyRtZtZbnypeCrtlVa3rGlr7SltVx+JnOJ+NuCqvd4NP+4stzp93ne6x74b1NCu9t6nukqzP5anfWs3rv+nAcQDVr4qnTQMrkOva5fwpFFSnvAAj5LxVSYa2lge5DzaZWi3Nozc54B8khKIHz8b3emz7xf7Fve2W91rJea9F5lC2EyD+q1sxwF0zWO5YF9x2+PHfGv9SKT/XRX2RybavTxfbQvxW5PpXV0qyOI9Tyj0+e+QNvF1WSijZHR/a5Xz2u18/SuVkyNc3qOtoedEfR5GjS3Wp7gVpb+oxjes/P7qyJatsiUXBM1mpmtThHpNRzv3zE/fIREeSLrLJqrSIlcue/5v4w6eRns/borD1i7Uz368dlvdZ2vz8JX14oszzngDvvFXvwhJO/3oBb3IVvlXni8aADwOwAGvxS5bUzp+VT+Gup0Nqd/x+14A2dtVvWbm6PfNhqWfQVbtn8bFHJxv4SACFqOHYsdV6/xnPVKyIhtZR/Gp9sdRttdRutVn3hfHDXmQYCFa++zhvj1YY5v7aDGe68V/S+DZ7rpxQ9lzqNPBkAUtpdLi26qYIc56WR+uD2E5s6uMOd+bQ+sNVz1b+L9RtcXuqppTbOdSaP+23ODJ25zi3LombFrpRlcu0z/tu9G5wP7gr5T+nOe8XuO15Urfnr75ViD7zd/fzBst1ZlP/8jiH+pUJ5/R/2WiqEcKc/6s554beyO5PHee9fVmQ+H1m/DU0ZXUCmJ9j6b33/PNv97tUA23Sr43DvjR+X2rN/YuObvvut9T/1G9WWBUXPpqY9TqnQ7U42ZL+dCT9M/u28Ormp5dOKT35gtexX2o1Pofu/24KdMamk9v/YwSJP1K0eV3r+8I7Vd7zV4hxZo1EkemkLctxZE0+7hTv79zK1QUx3AYX8lwpl+x/uWno8P+ad3lnky9fbfiy6J1G89jUBEAv3ATkH3M/+r/ChDs6kq925L+vtS0peV0imtbMH3RHQlou1/if+vmmen16UX++mZe2zAt+U2jC36J+SapT8PFatnaGP7Atpirpq9fSiNS/9As+lT3hu+Mh739K4x7d775rrGTPR6jY6wOw0uQlY+IY+tPOUu9+4WF89OPS/VAgDIMy1VAihVk8Xyi36FcXX0inWDQW6gEyuttS6mWLdTFcIIS1Zq5ls2tNKH2S1G1L8IYHde5z71WPFa2exyprh/+9ZfhaEkgmp+njwJNX095EzbWqPn00l1dR52Wfcqx1LQ9/4fvWEbHmurFb/DNWwiqyfLuunWz3HCl+eO/8195snQ39h6/rcr5849QGj1X2MnPdyiL8lgmNOwvFLhUyYa6kQQu/d4Oevfp4eSQHuAEJ65im9f4taMsV56w++J3qfdl15XEI1WbdVANs5UyNiUGVD1h0RjotKnZ3hPH+hWvV5qaEovAn2+bcV7xQOzSXz8o91xppTG2t72P3mm7P9XD/J+OTIVcNovfyPQC0VQoj8I/5+YyVAAESuRh/e7c582k9DULV26ReLZ3itTFbzM4pD//YQ4thBf5tqcIav8PN37W8Lp1xDhWWpPJ2d4bx1ve/R7s5Hf1XLp+nMdSUsmmF1uMhqcXYYdkK70x897YvaDZFNuxu2XHF+XiaQdVpFrvJFft3swIW7lgrhf5FFJnoiAEJzK18/3XPli7JG49L/qb8LMR1AD4ZsfZ7/v7cs9tpkzsHfHjwUn3+mhE35eQMz97Ao8c46wJbUOAbUwjedd2/wPX1e4b1NfA+19708yv36ieK7JNsOCctNwPrZ+vRn7MWn/PPD31ofslrR/JbN+xZ/8hnaAxieq5jQ70xU1FIQAGVIANvqdrn3bws8YybKxl1KOohdR/v5a87+0o9+y/7Fhy1bbc63mvct2mxtX3zy1MpYLXKKXhzZfccXzyqr08WyUeeim9oYijHRxS7eZVLNoLu/tdZH9+utC91ZE53P/q/oBqs3DNMP63z5/4Juzvy9MSDbDDztf3vjPcMfjOgBDNkRCf3OREUtBQFQVsenKLnta++EefaIf1htB8tazUR8srBsUbWm1eZ8zx/esbqNLn7B7vcKqFgTIj3j37T73yCrpQnbK6ul2f1v8Fw72c9166rPT+vHOOWlsBPiUzw3f2Z1v0JWrSVsr6zR2B50h2fsS3429dMHITgsecW6X48Pqqla0+8DDM+1k60eVwpPlTPXxGL96WGYDfTE8dv5U/FRSaXIzSre4W6f8wd7wC0isbrwJljN+3pvnFa8IQvVAQyvcOxMNNRSlIZRQAHfD9RrY9drI/rfGFA/w6rP/XdQFheXaI94yB7xUIndJplq5WenbX/2s3bPsUXGt8lq9T2/e76Us3LHsoBesCz17P5lo5+sHHTHqeNf9f7Nvn+e/evRa+3pcJEY9ahaP1tt/l5nrBaHdum8bCGlTK4tW5/vKbZcl94fxjXc3emPWW2HCMsOoshbfpBF3mySln3R3+2L/h6BAxjeHqDw7Ey511IQAOUh/6jfx8LmrdWHd586n6UQQucccKbc4rl2UnD36TkHnfduDE2TcXCHPrQzoAckp6qSZHUaaXUaGUDj4ari14+hbPI2qaVTrZ5jg/gVFr1tFX+1NcIHMExHIzw7U+61FHQBRVxhrm/yuJKXtjjZpsx9WRTklPJvvnlKrfNzNaRWT3em3l7CQJqiZ2NWhm/S2BAukaHm/yeMV+jf/Evv2xjWH8qd8WTgR08IobcsUMunlXJMNswJfMnJsB7AKPk1y72WggAwvX7Zt8F5/Vr100f+hxv7re7rZ/ueGai3Lgz0K7Yv9r1y6RlbOl+e++kD7jdPnvHrlk71PTdEbZpfWlPnU4vf8z0zQO9aEcoG9PtJalnoO2r10f3O+3e4s54N+++bneF+/9+gPuK8f7ta8/UZfgzHnfdvZ/I4v+OFInkAo+rXLPdaipLRBVRijVzztVrztbBsWb+d1ayXTGsrazUTNRrLKlVFlSShlCjI0TkH9b71etdKteozgysXvXul75nzra6XWe0vlA3ay6q1hFOgD+9W62aqhW+VuiSkzlznvDpa1k+32g+TzXrJWscX20sQ+Tk695DOWKu3LVIrPwvLG0NaOVNusZa+b3W/QjbuIlPqirikMz0z9D1/oazXRtZPt+qlizotZVJ1kVBNxqeIKknCKdD5R8WhXXrverVxrlo7M7RTgZb0C89+3u51dRALFfjyndevtdoNsbqNkU26yaq1ROExnZWhNsxRS6bofZvCdwDDf70Txp0pz1qKEsmCu+pwFCIj2DVUAYAuIAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAUBTvAQAAdwAAAAIAAEAAAAAIAAAAAQAAIAAAADGJ9QCASGNicBAAqDSklA07Wc16ybN6y5rNRGKqTKwupKXzj4gj+3TGGrVzmV4zQ2dncqgAAgAVpn7FWV1H2+feIOu19pMLVWuJqrVkWjur+xhxyRNq60I172W1bpbQmiMHEACI5ev+em08416TdVsFeJdgNe9rNe/re6y7PrSLowcQAIhVVpdLPFc8JzxVOBQAAYDK1Pq36u/53QvC9nIoAAIAlYis0chzzST/rX/OQXfhG2rDXHFgq87NEnGJMqm6rJcum3S1OgyXtZtz9AACADHMHnqviE8u/ne15H/OtHtFYe7JP+Uf0flH9MEdYs3X7vTHZJPu9sDbS3gCLOunW+2Gyma9ZO3mMjFVxCWK/KP62CGdsUZvW6xWfqqP/lLSnlVJkvXSZVpbq347UbeVTKkrq9YU3kRh2aIwVxfkiEM7deY6tXGeWjdTuL6A0i65tuww3GrSXTboIJKqy4RU4Rbq7Ey9bbFaMU1tmh/0zVO7IVbnUbJxV5lSVyhXZ2WoTfPU/Nf0wR1ULYT+co3poBHK+lS3lXfCPCGLvmCoFr7lfHS3+WbrtbFHPmy16l/SP3J9atkHzhcPidws/xc7f/7QatkvoO87dsj54mG1ZEpJu5RS177o71bnUSX0dOnMte6nD6jNPxT5u9/3APS+TZ4rJsqmPf0WzflwglryPyoYQos3gRHS+tRxRPHWXx/Y5nxyn/k2u1/h/cuMUlp/IYTttXqO9d45RzbsVNZiJNXwXPGsPfzBM+5S+iDvhHlWt8tLfs4h67f1XPdGQAnXuKv31i/8t/5CCNvrGfOs1eZ8KhgIAERxfWoz0M/167xXAuxR8bPB9sM8VzwrvPGB3iukpnmvnyJrNil7WezzbrLaDfGzSy3O9lz3hkisHsLjZp9/WykblNK+5PHi4QqUBc8AEDpSykZ+rr712pmG26tay3PlS0G3elVresa+7HvhIr//UR/aqZZP09uX6My1Oi9b+PJEXJKs2cRqc7494BYRn3Jau3zBXWrNjNM+n1DtjI+4w310aza1WpyjNn1HRQMBgOiTWF1YRWuUzjmgszMML/8H3i6qJBXd4JF97leP6/WzdG6WTE2zuo62B91RpEWWTbpbbS9QRYJn/2bn+/+qtTOKPmfOP6L3/Ozu+Vlt/sF765enbadhJ5lSVx/Zd8ql+q1+L9XV+m/Vwjf1ruX62CFRpaqV1lZ2GG73HBtEabV25/9HLXhDZ+2WtZvbIx+2Wp5bNAOany0IABAAiMYbgKo1/fz12CHj+wm7y6VF/1iQ47w0Uh/cfqLNPLjDnfm0PrDVc9W/i4ZH18uLBIDz8T2ltMA7luqjv8jk04ZFyMZd9SnTtFndxhT/oPv5P9x5r5z837mH1eYfxOYf1KyJJTxIKLqR6Y+6c144sSeZ65zJ47z3L5NVa522M/XbUM1AACB2mE7sI+u3E8USxf1h8m+t/8mr7+XTdP8bizz7PdOAH1m7udV2sGzSXdY+SybXFVUShSdeSHnG/TilCZb128qUukW/fc2M01r/U4t+9Bdnys0BHaSDO9x5L5/2J1++3vaj7HBaR5YM6YMHgABA6Jr6nIN+/ppUwzAAap/l5ys2zPH7j9WGuXaRwT9JNURCNZGXfXKDqQ3sSx6z2g0NbjdOeSrg91U1tfjdsh86tXq6UG7RwhafHrVYhxhAACA65GYJ5QrLPq0BTa4tq9U3meo5yU+Hks7y/zhBZ+3x03Yn1dS/BoCs2cRz8+fFr99Ld2px/PVx6V82hyA7927w81dfXvEyUcsQQowqQwhvAZTevdJPQ9z2ghB+h9nH7NFPm7T+gbS/IZm8Ov+Iv/sCRZ0CdwCIGWr9bLtx16KNb/+b1OIpQb8KcMxPh5JMbeB3UgSZ2sBPy/zrFmSNxsUfCejsTHfm03rjXH3kF+EUHP+j94Gf/G7qhJwDfr66bkt9YGvZszNc0QJwB4AIBcCqz4s3W7JWM8/F/y/oJvHANj+tbevz/Nfj4u8J5x7+7QGALJZJQghn0tVq0dv60K7fWn8hrZKfsur9W/x8dVBjPQECABWV3rtBrZjmp571He+5/BnhTSjhs7JJd8/v35bVG57YVMZqUeypst13vKzRuOjGO10sG3UuGkUbT46XLzKYUggh8o/qjNVFt9O8r4hLLKl0mWtPfSfgxKfaDbX7/dH/BxJSPWMmUitAAKCycL96TBTk+Klqva7y3rfEHny3bNpDVK0pLI+IT5Y1GlvthtjD7vP+7QfvrV9abQefHJGptbv846JbiU/x3PyZ1f0KWbWWsL2yRmN70B2esS/5uRf56YOTDXfBsWLbSS4aJPEp9qjHSr/FWTq1+B/tix/x/OFdq+1gmVxbWB6RkCqb9rAveiDu/iVWx+FUCUQtngEg1DcBh3Y5b/7Bc/27xd8Klsm17cET7METAtyUmv2s3XNskbGPslp9z++eL2Ufdiw79S0wvednP1V//FvuZ39XO5cLIayW/ewL75d1WpYeb3NetHuPK/4ysJU+yEof5OcDfp/uAtwBoKJSG+c6U2452bdunCU5B5wpt/h/QFqCnIPOezeetp2M1cUzQNZP9/z5w7hHt8Q9usVz3RuBtP5CCJGX7bx1vfHcdgABgEqQAcun+Z4bovdtLOt2Vk93pt4eeJborAzfpLHFRwo5H/211I2oJVP8vk9Q9J9t/t55Y/yZVh0ACABA6Mx1vokDnffvCCgGtNZbFjiTx+nDu4s2uEun+p4bUvrqWq5PLX7P98wAvWuFn83v/MmZdPUZJyZyfe6sic77dwY48lKtm+l7qr9a9mHJtwI6c53zxnXUBEQtngEgnJxCtfg9tWSKbNjJOqu3bNZb1momElNlYnUhLZF3RB/ZqzPXqh1L9ZoZJbwtrDPXOa+OlvXTrfbDZLNestbxJSETRH6Ozj2kM9bqbYvUys+KD9E5rdXe9F3hE33sPtda7QbLOi1EXJLOyxaHd6sNc9Wy9/0O8SypcT+y15lys/ziH1bHEfLEkpA1ZEI14RTq7IzjS1SqTd8xlh/RjCUhAaCSogsIAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAAAIAA4BABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAAAIAAEAAAAAIAAAAAQAAIAAAAAQAAIAAAAAQAAAAAgAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAQAAAAAgAAAABAAAgAAAABAAAgAAAABAAAAACAABAAAAACAAAAAEAACAAAAAEAACAAAAAEAAAAAIAABAy/x90jMWZxCr3WQAAAABJRU5ErkJggg=="
st.markdown(f"""
<link rel="apple-touch-icon" href="data:image/png;base64,{_ICO}">
<link rel="icon" type="image/png" href="data:image/png;base64,{_ICO}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Carboo">
<meta name="theme-color" content="#f97316">
<meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)
# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key, default in [
    ("logged_in",    False),
    ("current_user", None),
    ("module",       "menu"),
    ("toon_landing", True),
    ("_ls_checked",  False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── AUTO-LOGIN via localStorage ─────────────────────────────────────────────
if not st.session_state.get("_ls_checked") and not st.session_state.get("logged_in"):
    _saved_uid = st.query_params.get("_uid", "")
    if _saved_uid and len(_saved_uid) > 10:
        try:
            from login import _get_user_by_id
            _auto_user = _get_user_by_id(_saved_uid)
            if _auto_user:
                st.session_state.logged_in    = True
                st.session_state.current_user = {
                    "id":      _auto_user["id"],
                    "name":    _auto_user["naam"],
                    "email":   _auto_user["email"],
                    "role":    _auto_user["rol"],
                    "credits": _auto_user.get("credits", 0),
                }
                st.session_state["toon_landing"] = False
                st.session_state["_ls_checked"]  = True
                st.query_params.clear()
                st.rerun()
        except: pass
    st.session_state["_ls_checked"] = True

# JS: lees localStorage en stuur als URL param
if not st.session_state.get("logged_in"):
    st.markdown("""
    <script>
    (function() {
        var uid = localStorage.getItem('carboo_uid');
        if (uid && uid.length > 10) {
            var url = new URL(window.location.href);
            if (!url.searchParams.get('_uid')) {
                url.searchParams.set('_uid', uid);
                window.location.replace(url.toString());
            }
        }
    })();
    </script>
    """, unsafe_allow_html=True)


# ─── NIET INGELOGD → LOGIN PAGINA ────────────────────────────────────────────
if not st.session_state.logged_in:
    if st.query_params.get("actie") == "disclaimer":
        st.query_params.clear()
        render_disclaimer()
        st.stop()
    if render_wachtwoord_reset():
        st.stop()
    if st.session_state.get("toon_landing", True):
        render_landing_page()
        st.stop()
    render_login_page()
    st.stop()

# ─── INGELOGD ─────────────────────────────────────────────────────────────────
user = st.session_state.get("current_user")
if not user or not st.session_state.get("logged_in"):
    render_login_page()
    st.stop()
naam     = user.get("name", "Atleet") if user else "Atleet"
is_admin = user.get("role") == "admin" if user else False

# ─── Abonnement check ────────────────────────────────────────────────────────
_uid = user.get("id", "") if user else ""
_abo = get_abonnement(_uid) if _uid and not is_admin else {"fueling":True,"gut":True,"rapport":True,"trial":False,"alles":True,"dagen_resterend":999}

# Trial of abonnement verlopen → keuzemenu tonen
if not is_admin and not any([_abo["fueling"], _abo["gut"], _abo["rapport"]]):
    _email = user.get("email", "") if user else ""
    render_abonnement_keuze(_uid, _email)
    st.stop()

# Trial melding
if _abo.get("trial") and not is_admin:
    dagen = _abo.get("dagen_resterend", 0)
    st.markdown(
        f'<div style="background:#1a1200;border-left:3px solid #fbbf24;padding:8px 14px;border-radius:0 6px 6px 0;margin-bottom:12px;">'
        f'<span style="font-size:0.78rem;color:#fbbf24;">⏱️ Gratis proefperiode — nog <b>{dagen} dag(en)</b> resterend.</span></div>',
        unsafe_allow_html=True)


# HEADER
st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between;
            background:linear-gradient(135deg,#1e293b,#0f172a); border-radius:16px;
            padding:16px 24px; margin-bottom:20px; border:1px solid #334155;">
  <div style="display:flex; align-items:center; gap:14px;">
    <img src="{CARBOO_AVATAR}" style="width:44px; height:44px; border-radius:50%;
         border:2px solid #f97316; object-fit:cover;">
    <div>
      <div style="font-size:1.5rem; font-weight:900; letter-spacing:3px; color:#f8fafc;">
        CAR<span style="color:#f97316;">BOO</span>
      </div>
      <div style="font-size:0.68rem; color:#64748b; letter-spacing:1px;">SPORTS NUTRITION COACH</div>
    </div>
  </div>
  <div style="text-align:right; font-size:0.82rem; color:#64748b;">
    Ingelogd als <b style="color:#f8fafc;">{naam}</b>
    {'&nbsp;&nbsp;<span style="background:#f97316;color:white;border-radius:4px;padding:1px 7px;font-size:0.72rem;">ADMIN</span>' if is_admin else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# Toon openstaande coach uitnodigingen
if not is_admin:
    render_coach_uitnodigingen(_uid)

# Sla user_id op in localStorage voor auto-login
if st.session_state.get("logged_in") and st.session_state.get("current_user"):
    _uid_save = st.session_state.current_user.get("id","")
    if _uid_save:
        st.markdown(f"""
        <script>localStorage.setItem('carboo_uid', '{_uid_save}');</script>
        """, unsafe_allow_html=True)

# ─── NAVIGATIE / MODULE ROUTING ───────────────────────────────────────────────
_credits = st.session_state.get("current_user", {}).get("credits", 0)
nav_cols = st.columns([6, 1, 1, 1]) if is_admin else st.columns([7, 1, 1])
with nav_cols[-3] if is_admin else nav_cols[-2]:
    st.markdown(
        f'<div style="background:#0f172a;border:1px solid #334155;border-radius:8px;'
        f'padding:6px 12px;text-align:center;">'
        f'<div style="font-size:8px;color:#64748b;font-weight:bold;">CREDITS</div>'
        f'<div style="font-size:16px;font-weight:900;color:#f97316;">{_credits}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
with nav_cols[-2] if is_admin else nav_cols[-1]:
    if is_admin:
        if st.button("⚙️", key="nav_admin_top", help="Admin panel", use_container_width=True):
            st.session_state.module = "admin"
            st.rerun()
with nav_cols[-1] if is_admin else nav_cols[-1]:
    if st.button("↩️", key="nav_logout_top", help="Uitloggen", use_container_width=True):
        # Wis localStorage
        st.markdown("""
        <script>localStorage.removeItem('carboo_uid');</script>
        """, unsafe_allow_html=True)
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

module = st.session_state.module

# Controleer of gebruiker terugkomt van Mollie betaling
controleer_betaling_url()

if module == "menu":
    st.markdown("""
    <div style="text-align:center;padding:16px 0 20px;">
        <div style="font-size:0.7rem;color:#64748b;letter-spacing:3px;margin-bottom:6px;">
            JOUW NUTRITION TOOLS</div>
        <div style="font-size:1.3rem;font-weight:800;color:#f8fafc;">
            Kies een module om te starten</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fueling (bovenaan) ────────────────────────────────────────────────────
    if is_admin or _abo.get("fueling"):
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1e293b,#0f172a);
                    border:2px solid #22c55e;border-radius:16px;padding:24px;
                    margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:16px;">
                <div style="font-size:2.5rem;">⚡</div>
                <div>
                    <div style="font-size:1.2rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">
                        Fueling — Energie Coach</div>
                    <div style="font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                        TDEE · Trainingszone · Voedselbibliotheek · Dagschema · Dashboard
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚡  Start Fueling", key="open_fuelc_top", use_container_width=True):
            st.session_state.module = "fuelc"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Race Nutrition Plan ───────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a);
                border:2px solid #f97316;border-radius:16px;padding:24px;
                margin-bottom:6px;">
        <div style="display:flex;align-items:center;gap:16px;">
            <div style="font-size:2.5rem;">🏁</div>
            <div>
                <div style="font-size:1.2rem;font-weight:800;color:#f8fafc;margin-bottom:4px;">
                    Race Nutrition Plan</div>
                <div style="font-size:0.82rem;color:#94a3b8;line-height:1.6;">
                    Carboloading · Laatste maaltijd · Uur-per-uur raceplan · PDF rapport
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏁  Start Race Nutrition Plan", key="mod_coach",
                 use_container_width=True):
        st.session_state.module = "coach"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    # ── Coach Dashboard ───────────────────────────────────────────────────────
    if is_admin or user.get("role") == "coach":
        st.markdown("""
        <div style="background:#0f172a;border:1px solid #3b82f6;border-radius:12px;
                    padding:18px;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:1.8rem;">👥</div>
                <div>
                    <div style="font-size:0.95rem;font-weight:800;color:#f8fafc;margin-bottom:3px;">
                        Coach Dashboard</div>
                    <div style="font-size:0.78rem;color:#64748b;">
                        Atleten beheren · Welzijn opvolgen · Dagboek check</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👥  Open Coach Dashboard", key="open_coach_dash", use_container_width=True):
            st.session_state.module = "coaching"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)


    # ── Admin modules ─────────────────────────────────────────────────────────
    if is_admin or _abo.get("gut"):

        # Train the Gut
        st.markdown("""
        <div style="background:#0f172a;border:1px solid #8b5cf6;border-radius:12px;
                    padding:18px;margin-bottom:6px;">
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:1.8rem;">🧪</div>
                <div>
                    <div style="font-size:0.95rem;font-weight:800;color:#f8fafc;margin-bottom:3px;">
                        Train the Gut</div>
                    <div style="font-size:0.78rem;color:#64748b;">
                        Systematisch de maag trainen met oplopende KH-hoeveelheden.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧪  Open Train the Gut", key="open_testing",
                     use_container_width=True):
            st.session_state.module = "testing"
            st.rerun()


elif module == "coach":
    render_coach(user)

elif module == "carbomax":
    render_carbomax()

elif module == "raceprep":
    render_raceprep()

elif module == "optimeal":
    render_optimeal()

elif module == "admin":
    render_admin_panel()

elif module == "fuelc":
    if is_admin or _abo.get("fueling"):
        render_fuelc(user)
    else:
        st.warning("⚠️ Fueling is niet inbegrepen in je huidig abonnement.")
        render_abonnement_keuze(_uid, user.get("email",""))

elif module == "coaching":
    render_coach_dashboard(user)

elif module == "testing":
    if is_admin or _abo.get("gut"):
        render_testing(user)
    else:
        st.warning("⚠️ Train the Gut is niet inbegrepen in je huidig abonnement.")
        render_abonnement_keuze(_uid, user.get("email",""))

elif module == "rapport":
    html = st.session_state.get("rapport_html", "")
    if not html:
        st.session_state.module = "coach"
        st.rerun()
    else:
        data     = st.session_state.get("coach_data", {})
        atleet   = data.get("atleet_naam", naam).replace(" ", "_")
        wedstrijd= data.get("wedstrijd_naam", "race").replace(" ", "_")
        pdf_naam = f"Carboo_RacePlan_{atleet}_{wedstrijd}.pdf"

        from login import get_credits, gebruik_credit
        _uid = st.session_state.get("current_user", {}).get("id", "")

        if st.session_state.get("bevestig_nieuw_plan"):
            st.warning("⚠️ Ben je zeker? Je huidige rapport verdwijnt en je hebt een nieuwe credit nodig.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Ja, nieuw plan starten", key="bevestig_ja",
                             use_container_width=True):
                    wis_keys = [k for k in list(st.session_state.keys())
                                if k.startswith(("cl_","rp_","rd_","p_","w_","prev_",
                                                 "coach_stap","coach_data","rapport",
                                                 "bevestig"))]
                    for k in wis_keys:
                        del st.session_state[k]
                    st.session_state.module = "coach"
                    st.rerun()
            with c2:
                if st.button("❌ Annuleren", key="bevestig_nee",
                             use_container_width=True):
                    del st.session_state["bevestig_nieuw_plan"]
                    st.rerun()
            st.stop()

        if st.session_state.get("rapport_ontgrendeld"):
            credits_nu = 1
        elif "rapport_credits_gecheckt" not in st.session_state:
            credits_nu = get_credits(_uid) if _uid else 0
            st.session_state["rapport_credits_gecheckt"] = credits_nu
        else:
            credits_nu = st.session_state["rapport_credits_gecheckt"]

        if credits_nu <= 0:
            st.markdown("""
            <div style="background:linear-gradient(135deg,rgba(249,115,22,0.15),rgba(30,58,138,0.15));
                        border:2px solid #f97316;border-radius:12px;padding:20px;text-align:center;
                        margin-bottom:16px;">
                <div style="font-size:1.5rem;margin-bottom:8px;">🔒</div>
                <div style="font-size:1.1rem;font-weight:900;color:#f8fafc;margin-bottom:6px;">
                    Jouw rapport staat klaar!</div>
                <div style="font-size:0.85rem;color:#94a3b8;margin-bottom:4px;">
                    Koop een credit om te downloaden.</div>
            </div>
            """, unsafe_allow_html=True)

            col_koop, col_terug = st.columns([2, 1])
            with col_koop:
                if st.button("🛒  Koop credit & download rapport", key="koop_unlock",
                             use_container_width=True):
                    from login import sla_coach_data_op
                    sla_coach_data_op(_uid, data)
                    st.session_state["rapport_html_pending"] = html
                    st.session_state.module = "credits"
                    st.rerun()
            with col_terug:
                if st.button("🔄 Nieuw plan", key="rapport_terug_blur",
                             use_container_width=True):
                    st.session_state["bevestig_nieuw_plan"] = True
                    st.rerun()

            blurred_html = html.replace("</body>",
                """<style>body{filter:blur(5px)!important;pointer-events:none!important;
                user-select:none!important;}</style>
                <div style="position:fixed;top:0;left:0;right:0;bottom:0;
                            background:rgba(15,23,42,0.5);z-index:9999;
                            display:flex;align-items:center;justify-content:center;">
                    <div style="background:#1e293b;border:2px solid #f97316;border-radius:16px;
                                padding:30px 40px;text-align:center;max-width:400px;">
                        <div style="font-size:2rem;">🔒</div>
                        <div style="font-size:1.2rem;font-weight:900;color:#f8fafc;margin:10px 0 6px;">
                            Jouw rapport staat klaar!</div>
                        <div style="font-size:0.85rem;color:#94a3b8;">
                            Koop een credit om te downloaden.</div>
                    </div>
                </div></body>""")
            st.components.v1.html(blurred_html, height=2000, scrolling=False)

        else:
            if not st.session_state.get("rapport_credit_afgetrokken"):
                gebruik_credit(_uid, "Race Nutrition Rapport gegenereerd")
                st.session_state.current_user["credits"] = get_credits(_uid)
                st.session_state["rapport_credit_afgetrokken"] = True
                st.session_state["rapport_ontgrendeld"] = True

            col_terug, col_pdf = st.columns([1, 1])
            with col_terug:
                if st.button("🔄 Nieuw plan starten", key="rapport_terug"):
                    st.session_state["bevestig_nieuw_plan"] = True
                    st.rerun()
            with col_pdf:
                if st.button("📄  Download PDF", key="rapport_dl_pdf_btn",
                             use_container_width=True):
                    with st.spinner("PDF wordt gegenereerd..."):
                        try:
                            from carboo_coach import _genereer_pdf
                            gn = st.session_state.get("current_user",{}).get("name","Atleet")
                            data_pdf = dict(data)
                            data_pdf["logo_b64"]  = st.session_state.get("coach_logo_b64", "")
                            data_pdf["logo_mime"] = st.session_state.get("coach_logo_mime", "image/png")
                            pdf_bytes = _genereer_pdf(data_pdf, gn)
                            st.session_state["rapport_pdf"] = pdf_bytes
                            st.rerun()
                        except Exception as e:
                            st.error(f"PDF fout: {e}")
                if st.session_state.get("rapport_pdf"):
                    st.download_button(
                        label="⬇️  Sla PDF op",
                        data=st.session_state["rapport_pdf"],
                        file_name=pdf_naam,
                        mime="application/pdf",
                        use_container_width=True,
                        key="rapport_pdf_save"
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            st.components.v1.html(html, height=3000, scrolling=True)

elif module == "credits":
    _uid   = st.session_state.get("current_user", {}).get("id", "")
    _email = st.session_state.get("current_user", {}).get("email", "")
    render_credits_kopen(_uid, _email)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Terug", key="credits_terug"):
        st.session_state.module = "coach"
        st.rerun()
