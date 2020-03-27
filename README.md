# covid_plot
Draws plots of the number of confirmed cases and deaths from coronavirus disease (COVID-19), per country.

# Usage examples
```python3 covid_plot.py --list```

```python3 covid_plot.py --regions World```

```python3 covid_plot.py --regions Italy France```

```python3 covid_plot.py --regions Italy France --nonlog```

```python3 covid_plot.py --regions Italy France --forec_confirmed exp 7 20 --from_date 2020-02-01```

```python3 covid_plot.py --regions Italy France --nonlog --forec_confirmed exp 7 20 --forec_deaths poly 5 10```