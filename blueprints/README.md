# SALUS: minimumløbetid og forlængelse pr. rum

Kræver **v0.9.11b12** eller nyere. Tag en Home Assistant-backup før opdatering.

## Formularens opbygning

| Afsnit | Indhold |
|---|---|
| 1. Vejrudsigt og udeføler | Vejrtjenesten og en valgfri fysisk udeføler samlet øverst. |
| 2. Rum og komfortniveau | De rum, der styres, og niveauet ved ny tænding. |
| 3. Tænding og perioder | Prognosehorisont, tændgrænse, minimumløbetid og forlængelse. |
| 4. Slukning | Grænsen for den aktuelle udetemperatur ved periodens slutning. |
| 5. Rumtemperatur – valgfrit | Rumminimum og buffer. Foldes ud ved behov. |
| 6. Manuel styring og pause | Overtagelse og minimumspause. Foldes ud ved behov. |

Tænding bruger **altid timeprognosen**. Valget af temperaturgrundlag er fjernet.
Ved stop bruges udeføleren først; ellers vejrtjenestens aktuelle temperatur.
Formularændringen virker allerede med b12: **Importér igen** og genindlæs
automationer. En ny HACS-installation eller genstart er ikke nødvendig for
denne ændring, hvis du allerede kører b12.

Kilde- og grænsefelter beholder deres id'er. Det gamle `source_mode` kan ligge
i gemte input, men ignoreres af den nye skabelon. Har du tidligere valgt en
sensor som hovedkilde, skal du nu vælge en weather-entitet i feltet Vejrudsigt
og eventuelt flytte sensoren til den valgfrie udeføler, før reglen anvendes.

## Opdatér en eksisterende regel

1. Opdatér SALUS til **b12** i HACS, og genstart Home Assistant.
2. Åbn **Indstillinger → Automatiseringer og scener → Blueprints**.
3. Ved **SALUS – enkel gulvkomfort med slukgrænse og pause**: vælg **⋮ → Importér
   igen**, og bekræft. Opret ikke en ekstra automation for de samme rum.
4. Åbn din automation, gennemgå felterne, vælg din vejrtjeneste, og gem.
   Tænding bruger altid timeprognosen. De gamle maksimumfelter udgår;
   den nye minimumløbetid har sin egen standard på fire timer.
5. Genindlæs **Automatiseringer** under **Indstillinger → Værktøjer → YAML**.

[Importér skabelonen, hvis du ikke allerede har den](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FMichaelBusackBertelsen%2Fhomeassistant_salus%2Fblob%2Ffeature%2Ffloor-dashboard%2Fblueprints%2Fautomation%2Fsalus_comfort_rule.yaml)

## Den samlede regel

Prognosen bruges altid til at starte, ikke til at ændre en aktiv kørsel.
Aktuel udetemperatur bruges kun til stopvurdering ved periodegrænserne.
Alle grænser angives i Celsius; Fahrenheit-kilder omregnes.

| Hændelse | Beslutning for det enkelte rum |
|---|---|
| Startgrundlag under tændgrænsen, pause udløbet, rummet Fra | Tænd det valgte komfortniveau. |
| Samme betingelse, rummet manuelt tændt, overtagelse valgt | Bevar det manuelle niveau uden skrivning. Start minimumperioden nu. |
| Minimumperioden løber | Fortsæt, også hvis det allerede er varmt udenfor, eller prognosen ændres. |
| Perioden udløber, udetemperaturen er under slukgrænsen | Forlæng med den valgte periode, fx én time. |
| Perioden udløber, dette rum er fastholdt af sin egen minimumstemperatur | Forlæng kun dette rum. |
| Perioden udløber, det er varmt nok ude, og rummet behøver ikke fastholdelse | Sæt Gulvkomfort til Fra og begynd minimumspausen. |
| Målinger mangler ved stopvurdering | Forlæng dette rum og vis grunden i sporingen; ukendt er ikke varmt. |
| Manuel slukning eller niveauændring | Afslut ejerskab og begynd pause, så reglen ikke straks overtager igen. |

Der er **ingen maksimal køretid** i den nye logik. Minimumperiode og forlængelser
er beskyttede perioder: bliver det varmt midt i en forlængelse, sker automatisk
slukning først ved den næste periodegrænse. Manuel slukning virker straks.
Lav rumtemperatur kan kun holde en eksisterende kørsel aktiv; den tænder aldrig
komfort alene. Fra påvirker kun Gulvkomfort, ikke rummets normale termostat.

## Eksempel

Kl. 18 viser prognosen kulde om fem timer. Komforten starter, selv om det er
varmt ude nu. Med fire timers minimum vurderes første stop kl. 22, regnet fra
bekræftet aktivt niveau. Er det stadig under slukgrænsen, får rummet en ny time
til kl. 23. Bliver det varmt kl. 22.15, fortsætter perioden til kl. 23.

Hvis Stuen er under sit rumminimum, mens Hall er varm nok, kan Stuen fortsætte,
mens Hall slukkes. De deler hverken timer, ejerskab eller fastholdelse.

## Felterne

Alle felter har også forklaring og eksempler direkte i formularen.

| Felt | Betydning |
|---|---|
| Vejrudsigt | Weather-kilden til timeprognose ved start og aktuel reserveværdi ved stop. |
| Se dette antal timer frem | Prognosehorisonten ved nye starter. Påvirker ikke aktive perioder. |
| Rum med Gulvkomfort | En eller flere SALUS-selects. Kun én aktiv regel pr. rum. |
| Komfortniveau ved start | Niveau ved ny tænding. Overtagelse bevarer det manuelle niveau. |
| Tænd under | Strengt under, fx 4,9 kan starte ved grænse 5; præcis 5 kan ikke. |
| Minimumløbetid | Første beskyttede periode, fx fire timer. Erstatter ikke mindst-pausen efter sluk. |
| Forlængelse pr. vurdering | Fx én ny time, hvis der stadig er behov ved periodegrænsen. |
| Sluk ved eller over | Aktuel udetemperatur ved periodegrænsen. Skal være højere end tændgrænsen. |
| Udetemperaturføler (valgfri) | Fysisk sensor ved siden af vejrudsigtsvalget øverst. Prioriteres over vejrtjenestens aktuelle temperatur ved stop. |
| Hold aktiv ved lav rumtemperatur | Valgfrit. Bruger termostaten på samme enhed som det enkelte Gulvkomfort-select. |
| Minimum rumtemperatur | Fælles grænse for valgte rum, men hvert rum vurderes separat. |
| Buffer før rumfastholdelse frigives | Minimum 21 og buffer 0,5: et rum, der har været under 21, frigives ved 21,5. |
| Overtag manuelt aktiveret Gulvkomfort | Fra som standard. Overtager kun ved opfyldt startbetingelse og udløbet pause. |
| Mindste pause før ny start | Gælder både nye tændinger og overtagelser, separat pr. rum. |

Ændringer i minimum- og forlængelseslængde bruges ved næste nye kørsel; en gemt
aktiv periodes tidspunkter nulstilles ikke. Rumgrænser og udendørs slukgrænse
kan ændres og anvendes ved kommende vurderinger. Brug separate regler for rum
med forskellige temperaturgrænser. En manuel ændring til samme niveau kan ikke
opdages fra niveauet alene. At slå overtagelse fra igen frigiver ikke allerede
overtagne kørsler; sluk manuelt, hvis de skal afbrydes.

## Kilder og manglende data

Stopmåling prøver først den valgte udeføler. Er den ugyldig eller utilgængelig,
bruges den valgte weather-entitets aktuelle temperatur. Der vælges aldrig en
vilkårlig anden vejrtjeneste. Mangler begge, forlænges perioden. Fremtidig
prognose bruges aldrig som erstatning for aktuel stoptemperatur.

Rumminimum kobles automatisk via Home Assistants enhedsregister til den
tilhørende SALUS-termostat. Ingen entitets-id'er gættes ud fra navne. Mangler
der en entydig termostat eller en gyldig temperatur, og rumminimum er slået til,
forlænges kun dette rum. Med funktionen slået fra kræves ingen rumtemperatur.

## Sporing og genstart

Se automationens nyeste **Sporing → Resultat → Ændrede variabler**.

| Felt | Hvad det viser |
|---|---|
| `forklaring` | Hvorfor hvert rum tænder, overtages, venter, forlænges eller slukkes. |
| `taendgrundlag_c` | Den aktuelle startvurdering. Kan være `null`, når ingen rum er klar til start. |
| `slukgrundlag_c` / `slukdata` | Aktuel temperatur og den faktisk anvendte stopkilde eller manglende data. |
| `rum_og_timer` | En selvstændig post pr. rum med ejerskab, niveau, adoption, minimum og pause. |

I hvert rum viser `active_at` starten af minimumperioden, `minimum_until` dens
slutning og `next_check_at` næste stopvurdering. `adopted` viser overtagelse,
`room_hold` fastholdelsen og `room_temperature_source` den konkrete termostat.
`start_trigger_temperature_c` husker startgrundlaget fra nye starter/overtagelser.
En opgraderet gammel kørsel har ikke nødvendigvis denne historiske måling.
Der er ingen `maximum_stop_at` i minimumlogikken. Tider har tidszoneangivelse.

State gemmes pr. rum og overlever genstart. En overskredet periode vurderes én
gang med de aktuelle værdier, når HA og enheden er tilbage. Forlængelse regnes
fra denne vurdering, ikke ved at genafspille alle mistede timer. Nye prognoser
hentes ikke alene for at justere aktive rum.

En deaktiveret minimum-automation sender ikke automatiske stop eller nye starter.
Timerne fortsætter tidsmæssigt; ved aktivering vurderes en udløbet periode ved
næste tjek. Manuel styring virker fortsat. Ubekræftede kommandoer genafsendes
ikke automatisk. Backup, reparation og nulstilling fungerer som hidtil.

## Opgradering og tilbageførsel

HACS alene ændrer ikke din importerede skabelon. Gamle skabeloner beholder deres
maksimumlogik, indtil du importerer igen. En aktiv gammel kørsel konverteres én
gang med sin oprindelige kendte starttid, så opdateringen ikke giver en ny fuld
minimumperiode. Nye normalstarter venter på bekræftet aktivt niveau.

Gamle maksimum-input kan ligge i automationens gemte data, men bruges ikke af
den nye skabelon. Gennemgå og gem de nye felter; ingen ekstra automation behøves.
Ved tilbageførsel til en ældre beta skal HA-backup fra før b12 og den tilsvarende
gamle skabelon gendannes. Slet ikke aktive journaler eller genafspil rå snapshots.

Den [gamle vejrskabelon med tidsregel og døgnregel](LEGACY-WEATHER.md) er fortsat
bevaret separat. Klienten er stadig floor4 og ændrer kun komfortindstillingen;
den kunstige 255-spærring er fjernet, men fysisk tælleroverløb er ikke observeret.
