# JSON Registry Manager

[English](README.md)

**JSON Registry Manager (JRM)** je univerzální terminálový nástroj pro správu, validaci a verzování strukturovaných JSON registrů.

Není pevně svázaný s konkrétním typem dat. Pomocí souboru `registry.yaml` lze určit strukturu položek, povinná pole, validátory, lokalizované názvy a umístění JSON souboru.

Hodí se například pro seznamy chráněných domén, allowlisty, katalogy služeb, seznamy API endpointů, slovníky nebo další ručně udržované registry.

## Hlavní funkce

- interaktivní terminálové rozhraní
- angličtina a čeština
- automatická detekce jazyka systému
- trvalá volba `auto`, `en` nebo `cs`
- jednorázové přepnutí přes `--lang`
- přidávání, editace, mazání a hledání položek
- validace povinných polí
- kontrola unikátních ID a hodnot
- kontrola domén/hostname
- lokalizované názvy polí a hodnot výběru
- automatické vytvoření ID ze jména
- Git diff, commit a push
- neinteraktivní `jrm validate` pro CI
- připravená GitHub Actions workflow
- profil pro Phishing Domain Guard

## Instalace

Po zveřejnění repozitáře na GitHubu je nejpohodlnější `pipx`:

```bash
sudo dnf install pipx
pipx ensurepath
pipx install git+https://github.com/JN5555/json-registry-manager.git
```

Poté:

```bash
jrm --version
```

Pro vývoj:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Použití

V adresáři projektu musí být například:

```text
registry.yaml
protected-list.json
```

Pak stačí:

```bash
jrm
```

Příkazy:

```bash
jrm list
jrm validate
jrm search airbank
jrm add
jrm edit airbank
jrm remove airbank
jrm diff
jrm commit "Add Example Bank"
jrm push
```

## Jazyk

Automatická volba je výchozí. JRM kontroluje `LC_ALL`, `LC_MESSAGES`, `LANG` a systémové locale.

Trvalé přepnutí:

```bash
jrm language cs
jrm language en
jrm language auto
```

Pouze pro jeden příkaz:

```bash
jrm --lang cs validate
jrm --lang en validate
```

Nastavení se ukládá do:

```text
~/.config/json-registry-manager/config.toml
```

## Phishing Domain Guard

V adresáři:

```text
examples/phishing-domain-guard/
```

je připravený profil kompatibilní s projektem:

```text
https://github.com/JN5555/phishing-domain-guard
```

Stačí zkopírovat `registry.yaml` do kořene repozitáře Phishing Domain Guard:

```bash
cp examples/phishing-domain-guard/registry.yaml /cesta/k/phishing-domain-guard/registry.yaml
```

Potom v tomto repozitáři spustit:

```bash
jrm
```

Nástroj automaticky použije existující `protected-list.json`.

Při přidávání položky se zobrazí formulář například pro:

- název
- ID
- kategorii
- zdroj
- hlavní domény
- známé hosty / adresy internetového bankovnictví
- názvy značek a aliasy

Před uložením je celý registr znovu zvalidován.

U polí s validátorem `hostname` lze vložit i běžnou URL, například:

```text
https://online.example.cz/login
online.example.cz/login
```

JRM ji při interaktivním zadávání automaticky převede na uložený hostname:

```text
online.example.cz
```

Pokud validace přesto najde chybu, rozepsaná položka se nezahodí. JRM nabídne opravu se zachováním všech již zadaných hodnot.

## Git

JRM nepoužívá vlastní přístupový token ke GitHubu. Používá běžný lokální příkaz `git`.

Například:

```bash
jrm diff
jrm commit "Update protected domains"
jrm push
```

Použije se tedy stejné přihlášení, které již funguje pro `git push` v terminálu.

## GitHub Actions

Příkaz:

```bash
jrm validate
```

vrací při chybě nenulový návratový kód, takže jej lze použít jako kontrolu každého push/PR.

Ukázková workflow je součástí repozitáře v `.github/workflows/tests.yml`.

## Licence

MIT


### Nápověda a příklady u polí

Profil může ke každému poli přidat lokalizované vysvětlení a příklad. Jádro JRM tak zůstává univerzální, ale konkrétní formulář může být srozumitelný i netechnickému uživateli.

```yaml
fields:
  domains:
    type: list
    required: true
    validator: hostname
    label:
      en: Official main domain(s)
      cs: Oficiální hlavní doména / domény
    help:
      en: Main legitimate websites. Full URLs are accepted and normalized.
      cs: Hlavní legitimní weby služby. Lze vložit i celou URL.
    example:
      en: example.com
      cs: priklad.cz
```

Interaktivní formulář jasně označí povinná a volitelná pole. Volitelné položky lze přeskočit Enterem.


## Interaktivní rozhraní

Interaktivní rozhraní obsahuje adaptivní **Procházet položky**. Dlouhé registry se podle šířky terminálu zobrazí v 1–3 sloupcích. U velkých seznamů se při výběru používá filtrování psaním. Výsledky hledání jsou akční: vyberete položku a zvolíte **Zobrazit detail**, **Upravit**, **Odstranit** nebo **Zpět**.

