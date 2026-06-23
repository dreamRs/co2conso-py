import pandas as pd
import altair as alt
alt.data_transformers.disable_max_rows()

def courbe(donnees):
    now = max(donnees["date_heure_cet"])
    donnees = donnees[donnees["date_heure_cet"] >= now - pd.DateOffset(years=1)]
    donnees = donnees.set_index("date_heure_cet").resample("8h").mean(numeric_only=True).reset_index()
    donnees_long = donnees.melt(
        id_vars=["date_heure_cet"],
        value_vars=["intensite_emissions_conso", "part_enr_conso"],
        var_name="metrique",
        value_name="valeur"
    )
    donnees_long["metrique"] = donnees_long["metrique"].replace({
        "intensite_emissions_conso": "Intensité CO₂",
        "part_enr_conso": "Part ENR"
    })
    donnees_long["valeur_str"] = donnees_long.apply(
        lambda row: f"{round(row['valeur'], 1)} gCO₂éq/kWh" if row["metrique"] == "Intensité CO₂" else f"{round(row['valeur'], 1)} %",
        axis=1
    )
    donnees_long["couleur"] = donnees_long["metrique"].map({
        "Intensité CO₂": "#1565C0",
        "Part ENR": "#2e7d32"
    })
    selection = alt.binding_radio(
        options=["Intensité CO₂", "Part ENR"],
        name=" "
    )
    param = alt.param(
        name="choix",
        bind=selection,
        value="Intensité CO₂"
    )
    hover = alt.selection_point(
        on="mouseover",
        nearest=False,
        fields=["date_heure_cet"],
        empty=False
    )
    line = alt.Chart(donnees_long).mark_line(
        strokeWidth=1
    ).encode(
        x=alt.X("date_heure_cet:T",
            title="",
            axis=alt.Axis(
                format="%m/%Y",
                labelAngle=-45,
                labelOverlap=True,
                tickCount="month"
            )),
        y=alt.Y("valeur:Q", title=""),
        color=alt.Color("metrique:N",
            scale=alt.Scale(
                domain=["Intensité CO₂", "Part ENR"],
                range=["#1565C0", "#2e7d32"]
            ),
            legend=None
        )
    ).transform_filter(
        alt.datum.metrique == param
    )
    points = line.mark_point(
        size=80
    ).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("date_heure_cet:T", title="Date", format="%d/%m/%Y %H:%M"),
            alt.Tooltip("valeur_str:N", title="Valeur")
        ]
    ).add_params(hover)
    rule = alt.Chart(donnees_long).mark_rule(
        color="gray",
        strokeWidth=1
    ).encode(
        x="date_heure_cet:T",
        opacity=alt.condition(hover, alt.value(0.5), alt.value(0))
    ).transform_filter(
        alt.datum.metrique == param
    )
    return (line + rule + points).add_params(param).properties(
        width="container",
        height="container"
    )

def boxplot_annuel(donnees):
    donnees = donnees.copy()
    donnees["annee"] = donnees["date_heure_cet"].dt.year.astype(str)

    donnees_long = donnees.melt(
        id_vars=["annee"],
        value_vars=["intensite_emissions_conso", "part_enr_conso"],
        var_name="metrique",
        value_name="valeur"
    )
    donnees_long["metrique"] = donnees_long["metrique"].replace({
        "intensite_emissions_conso": "Intensité CO₂",
        "part_enr_conso": "Part ENR"
    })

    selection = alt.binding_radio(
        options=["Intensité CO₂", "Part ENR"],
        name=" "
    )
    param = alt.param(
        name="choix_box",
        bind=selection,
        value="Intensité CO₂"
    )

    chart = alt.Chart(donnees_long).mark_boxplot(
        outliers=False,
        size=30
    ).encode(
        x=alt.X("annee:O", title="Année"),
        y=alt.Y("valeur:Q", title=""),
        color=alt.Color("metrique:N",
            scale=alt.Scale(
                domain=["Intensité CO₂", "Part ENR"],
                range=["#1565C0", "#2e7d32"]
            ),
            legend=None
        )
    ).transform_filter(
        alt.datum.metrique == param
    ).add_params(param).properties(
        width="container",
        height="container"
    )

    return chart