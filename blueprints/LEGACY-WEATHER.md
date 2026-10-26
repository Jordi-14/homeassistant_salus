# Vejrstyret SALUS gulvkomfort

[Importér regelskabelonen i Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FJordi-14%2Fhomeassistant_salus%2Fblob%2Fmaster%2Fblueprints%2Fautomation%2Fsalus_floor_weather.yaml)

Bruges med SALUS-betaens Gulvkomfort-entiteter og Home Assistants almindelige
automationer. SALUS b5 behøver ingen ny installation eller genstart for at
bruge denne skabelon. Ingen konti, API-nøgler eller eksterne abonnementer tilføjes.
Vejrdata kommer fra en allerede konfigureret `weather`-entitet og/eller egen
temperaturføler. En prognoseregel kræver timeprognoser mindst 24 timer frem;
en ren temperatur-/tidsregel kan bruges alene med en udeføler.

## Opret din regel

1. Åbn importlinket, vælg din Home Assistant, forhåndsvis og importér skabelonen.
2. Vælg **Opret automation** og giv den et navn, fx *Gulvkomfort – badeværelser*.
3. Vælg de Gulvkomfort-entiteter, som skal følge samme regel.
4. Vælg din vejrudsigt. Vælg eventuelt din egen udeføler til tidsreglen.
5. Indstil temperaturgrænser, tidsrum og komfortniveauer og gem automationen.

Du kan lave flere automationer med forskellige rumgrupper. Et rum skal kun
styres af én aktiv vejrregel, så reglerne ikke modarbejder hinanden. Tidsregel
og døgnregel kan slås til/fra uafhængigt. Begge slået fra sender ingen kommandoer.
Brug automationens normale tænd/sluk-knap til at sætte al automatisk styring på
pause; det ændrer ikke det sidst valgte komfortniveau. Mens reglen er aktiv,
kan en manuel ændring blive erstattet ved næste vurdering.

## Eksempel – værdierne kan ændres i formularen

| Regel | Temperaturgrundlag | Betingelse | Resultat |
|---|---|---|---|
| Døgnregel, førsteprioritet | Højeste timeprognose de næste 24 timer | Alle timer under 5 °C | Niveau 1 hele døgnet |
| Tidsregel | Valgt udeføler, ellers vejrtjenestens aktuelle temperatur | Under 12 °C og kl. 06–22 | Niveau 1 |
| Ingen aktiv betingelse | Gyldige nødvendige data | Ingen af reglerne kræver komfort | Fra |

Grænserne er strengt *under*: præcis 5 °C tænder ikke en slukket døgnregel.
Standardbufferen er 1 °C: allerede aktive rum får en højere slukkegrænse,
så små temperaturudsving ikke giver gentagne skift. Bufferen beregnes ud fra
rummets aktuelle aktive komfortniveau, også når tidsreglen hidtil har holdt
det aktivt. Den er ikke en separat hukommelse for hver delregel.
Tidsreglen stopper ved sluttidspunktet, medmindre døgnreglen kræver komfort.
Fx kl. 22–06 virker over midnat; samme start og slut betyder hele døgnet.
Tider følger Home Assistants lokale tidszone. Temperaturer i °F omregnes til °C.

## Data, opdatering og fejl

Reglen vurderes hvert kvarter, ved start- og sluttidspunktet og ved Home
Assistant-start. Den henter timeprognoser med den almindelige
[`weather.get_forecasts`](https://www.home-assistant.io/actions/weather.get_forecasts/)
handling, kun når døgnreglen er aktiveret. Den læser ALLE relevante
temperaturer, ikke minimumstemperaturen. Den kræver mindst 24 forskellige
tidspunkter i horisonten, første punkt senest om en time, sidste punkt mindst
23 timer frem og højst en time mellem punkterne. Det er prognosens timeværdier,
ikke en garanti for den faktiske temperatur mellem opdateringer.

En aktiv døgnregel med manglende, ugyldige, for korte eller fejlede prognoser
sender ingen ændringer. En manglende valgt udeføler erstattes ikke lydløst af
vejrtjenesten: tidsreglen bevarer niveauet, når den behøver en temperatur.
Uden for tidsrummet kan tidsreglen slukke uden temperaturmåling, og en gyldig
døgnprognose kan tænde uafhængigt af føleren. Vejrtjenestens tilgængelighed og
prognosens tidspunkter kontrolleres; udbyderens interne udstedelsestid eller
følerens fysiske målekvalitet kan skabelonen ikke verificere.

En manglende entitet eller en `unavailable`/`unknown` Gulvkomfort-entitet
springes over. Uændrede niveauer sender ingen kommando. Skift går gennem
SALUS-integrationens eksisterende backup og fulde kontrol af tilbagemeldingen.
En skrivefejl stopper den pågældende kørsel uden automatisk genafsendelse eller
tilbagerulning; næste planlagte vurdering bruger de normale sikkerhedstjek.
Reglen overtager ikke fejlbehandling eller backup fra SALUS-klienten.

Se automationens **Sporinger** for data og stopårsag ved fejl.
Skabelonopdateringer hentes separat gennem Home Assistants blueprintfunktion;
en HACS-opdatering ændrer ikke en allerede importeret skabelon.

## Betabegrænsning

Den nuværende SALUS-beta understøtter fortsat kun den afprøvede termostatprofil
og stopper sikkert, når konfigurationstælleren når 255. Tælleroverløb er endnu
ikke dokumenteret eller afprøvet. Automatiske regler kan derfor endnu ikke
betragtes som en løsning til ubegrænset drift. Skabelonen ophæver ikke denne
grænse; flere gentagne kørselstjek er ikke flere skrivninger, når niveauet
allerede er korrekt. Håndtering af tællergrænsen kræver særskilt protokolarbejde.

## Verifikation

Skabelonen parses med Home Assistants blueprintparser, og handlingerne køres
i den rigtige scriptmotor med simulerede vejrdata og servicekald. Prøverne
ændrer ingen Home Assistant-installation, gateway eller termostat. Komplet
gennemgang af importformularen med brugerens konkrete vejrudbyder skal stadig
foretages ved opsætning.
