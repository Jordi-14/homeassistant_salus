# Enkel SALUS-komfortregel

**Kræver SALUS v0.9.11b11 eller nyere.** Opdatér integrationen i HACS og genstart
Home Assistant først.

[Importér den nye komfortregel](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FMichaelBusackBertelsen%2Fhomeassistant_salus%2Fblob%2Ffeature%2Ffloor-dashboard%2Fblueprints%2Fautomation%2Fsalus_comfort_rule.yaml)

## Sådan kommer du i gang

1. Opdatér til b11 i HACS og genstart Home Assistant.
2. Åbn importlinket. Hvis My Home Assistant spørger om adressen, angiv din egen
   Home Assistant-adresse (fx `http://10.210.0.225:8123`) og tryk Gem.
3. Importér **SALUS – enkel gulvkomfort med slukgrænse og pause**.
4. Vælg **Opret automation**, giv den et navn, og udfyld formularen.
5. Deaktivér en eventuel gammel komfortregel for de samme rum. Sæt manuelt
   aktiverede rum til Fra, og gem den nye automation.

Én aktiv regel pr. rum. Du kan lave flere regler til forskellige rumgrupper.
Indstillingerne ligger under **Indstillinger → Automatiseringer og scener**,
ikke i rumkortet. Åbn den oprettede automation for at ændre dem.

## Opdatér en eksisterende regel og se beslutningen

1. Opdatér SALUS til **v0.9.11b11** i HACS og genstart Home Assistant.
2. Åbn **Indstillinger → Automatiseringer og scener → Blueprints**.
3. Ved **SALUS – enkel gulvkomfort med slukgrænse og pause**: vælg **⋮ →
   Importér igen**, og bekræft. Importlinket ovenfor kan også bruges til at
   erstatte den eksisterende skabelon. Opret ikke en ekstra automation.
4. Genindlæs automationer under **Indstillinger → Værktøjer → YAML → Automatiseringer**.
   Dine eksisterende feltværdier og gemte timer bevares.
5. Vent til næste minuttjek. Åbn din automation → **Sporinger**, og vælg den
   nyeste kørsel. Klik på det sidste trin **Resultat – forklaring, temperatur
   og timer**, og derefter **Ændrede variabler**.

| Felt i sporingen | Hvad det viser |
|---|---|
| `forklaring` | Temperaturgrundlag og en dansk forklaring på hvert rums beslutning. |
| `taendgrundlag_c` | Minimum i de næste X timers prognose, eller aktuel temperatur ved målt kilde. `temperaturgrundlag_c` er samme værdi af hensyn til ældre opsætninger. |
| `slukgrundlag_c` | Den aktuelle udetemperatur nu. `null` betyder, at intet gyldigt aktuelt slukgrundlag er tilgængeligt. |
| `slukdata` | Kilde og status for den aktuelle udetemperatur, adskilt fra prognosens status. |
| `vejrdata` | Datastatus, prognoseperiode, tidspunkt for minimum, hentetid og om data kom fra cache. |
| `rum_og_timer` | Beslutning, eventuel sendt kommando, aktuelt rapporteret niveau, cyklusfase, slukfrist og pause for hvert rum. |

I `rum_og_timer` betyder `maximum_stop_at: null`, at der ikke er en aktiv
maksimal slukfrist. `next_start_not_before` er det tidligste tidspunkt for en
ny start; temperaturen skal stadig være lav nok. Tider har tidszoneangivelse.
`command: null` betyder, at denne vurdering ikke sendte en kommando. En rapporteret
værdi kan kortvarigt afvente enhedsopdateringen; det vises separat fra kommandoen.

Eksempel: **Temperaturgrundlag 8 °C – komforten fortsætter** med uændret
slukfrist. Næste minuttjek sender ikke en ny tændkommando. En for kort eller
fejlet prognose får sin egen forklaring og bliver aldrig vist som 0 °C.

Gamle spor indeholder kun de gamle input; vælg en kørsel efter opdateringen.
HACS-opdatering uden reimport viser ikke det nye Resultat-trin. Almindelige fejl
vises fortsat i handlingstrinnet, hvis vurderingen ikke kan gennemføres.

## Felterne

| Felt | Hvad du vælger |
|---|---|
| Temperaturgrundlag | Målt temperatur nu eller den laveste timeprognose i de næste timer. Dette bruges til tænding. Slukning bruger altid udetemperaturen nu. |
| Udeføler eller vejrudsigt | Din eksisterende sensor eller weather-entitet. Prognose kræver timeprognoser. |
| Se dette antal timer frem | Kun prognose. Fx 12 timer betyder kl. 18–06, hvis klokken nu er 18. Det kan tænde med det samme. |
| Rum med Gulvkomfort | De komfort-selects, der skal følge reglen. Hvert rum har sin egen timer og pause. |
| Komfortniveau | Niveau 1, 2 eller 3 ved automatisk start. |
| Tænd under | Fx 5 °C. Præcis 5 tænder ikke; 4,9 kan tænde. |
| Brug temperaturgrænse til slukning | Slå fra, hvis du kun vil slukke efter maksimal køretid. |
| Sluk ved eller over | Fx 7 °C. Skal være højere end tændgrænsen og gælder udetemperaturen lige nu, også ved prognosestyret tænding. |
| Brug maksimal køretid | Sluk efter et fast antal timer, også hvis det stadig er koldt. |
| Maksimal køretid | Fx 4 timer. Tiden regnes fra faktisk kommandostart og forlænges ikke af gentagne vurderinger. |
| Mindste pause før ny start | Fx 6 timer efter bekræftet Fra. Først derefter må kulden starte en ny kørsel. |

Er den aktuelle udetemperatur allerede ved eller over den aktiverede slukgrænse,
holder reglen rummet slukket, selv om prognosen er kold. Det forhindrer en start
fulgt af en øjeblikkelig slukning. Slukgrænsen skal være deaktiveret, hvis kun
maksimal køretid skal styre slukning.

Mindst én slukbetingelse skal være slået til. Når begge er til, gælder den første.
Alle felterne har også forklaringer og eksempler direkte i formularen.

## Eksempel

Tænd under **5 °C**, sluk ved **7 °C**, højst **4 timer**, pause **6 timer**:

- Kl. 18: prognosens minimum de næste X timer er 4 °C, og udetemperaturen nu er under 7 °C → Niveau 1.
- Stiger udetemperaturen nu til 7 °C kl. 20, slukkes dér, også hvis prognosen stadig er kold. Ellers senest omkring kl. 22.
- Ved bekræftet Fra kl. 22 kan kulden tidligst tænde igen kl. 04.

Der er hverken separat tidsregel eller døgnregel. Ved prognose kan en kold time
i den valgte horisont tænde komforten før kulden. Prognoser hentes højst hvert
kvarter, og den fremadrettede minimumsværdi vurderes hvert minut.

## Genstart, manuelle ændringer og fejl

Køretid og pause gemmes automatisk. En genstart starter ikke timerne forfra,
og der kræves ingen ekstra hjælpere. Mens HA er slukket, kan det ikke styre
termostaten; en overskredet frist behandles, når HA og enheden er tilgængelige.

Fra slukker kun Gulvkomfort. Rummets normale ønskede temperatur ændres ikke.
Et manuelt ændret niveau respekteres og starter pausen; et rum med manuelt
tændt komfort overtages ikke automatisk. En ny automatisk start kræver Fra.
En manuel ændring til samme niveau kan ikke skelnes fra det eksisterende niveau.

Slukker du automationen, forhindrer det nye starter. En allerede startet
**maksimal køretid gælder stadig**. Uden maksimal køretid stopper en deaktiveret
automation med at vurdere varmegrænsen; sæt selv Gulvkomfort til Fra ved behov.

Manglende/ugyldigt tændgrundlag tænder ikke. Mangler aktuel udetemperatur,
afventer temperaturslukning; en fremtidig prognose bruges ikke som erstatning.
Omvendt kan en gyldig varm udetemperatur slukke, selv om prognosen fejler.
Maksimal køretid kræver ingen vejrdata. Prognose kræver tilstrækkeligt mange
gyldige timepunkter i hele horisonten. Dataudbyderens faktiske målekvalitet eller
interne udstedelsestid kan reglen ikke kontrollere.

En utilgængelig enhed kan ikke garanteres slukket til tiden. Hvis en kommando
ikke kan bekræftes, gentages den ikke automatisk. Se **Indstillinger → System →
Reparationer**, kontrollér niveauet i SALUS, sæt komfort til Fra, og brug
handlingen **SALUS: Nulstil blokeret Gulvkomfort-regel** med automationen valgt.
Det starter en ny pause uden nye termostatkommandoer.

## Betabegrænsning og gammel skabelon

Klienten ændrer nu kun komfortindstillingen og kopierer tællerbytes urørte.
Den tidligere kunstige 255-spærring er fjernet. Enheden opdaterer selv de læste
tællerdata, som bekræftet i to hardwareforsøg. Et faktisk overløb er endnu ikke
observeret på hardware; grænsetests er simulerede. Firmwareafgrænsningen gælder
stadig. Uændrede niveauer giver ingen nye skrivninger.

Den [tidligere vejrskabelon med tidsregel og døgnregel](LEGACY-WEATHER.md) er
bevaret til eksisterende installationer. Den ændres ikke af denne udgivelse.
Den nye formular importeres separat; HACS ændrer ikke dine eksisterende regler.
