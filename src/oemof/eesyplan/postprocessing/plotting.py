import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from oemof.eesyplan.postprocessing.cost_calculation import _sum_columns_by_level


def plot_all_flows_plotly(all_flow_dict, storage_content=None, normalize=False, specific=True):
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "Flow (kWh)",
            "Variable Costs (propagated)",
            "Fixed Costs (propagated)",
            "Total Costs (propagated)",
            "storage content"
        )
    )

    colors = px.colors.qualitative.Plotly
    flow_colors = {}
    for i, flow_name in enumerate(all_flow_dict.keys()):
        flow_colors[flow_name] = colors[i % len(colors)]

    for flow_name, flow_data in all_flow_dict.items():
        df = flow_data["flow_df"]
        color = flow_colors[flow_name]

        label = f"{flow_name[0].label} -> {flow_name[1].label}"

        flow = df["flow_v"]
        mask = flow > 0.001

        if specific:
            var_cost = df["var_c_spec_p"].where(mask, df["var_c_spec_p"].clip(upper=1))
            fix_cost = df["fix_c_spec_p"].where(mask, df["fix_c_spec_p"].clip(upper=1))
            total_cost = var_cost + fix_cost
        else:
            var_cost = df["var_c_tot_p"]
            fix_cost = df["fix_c_tot_p"]
            total_cost = var_cost + fix_cost

        if normalize:
            if flow.max() != 0:
                flow = flow / flow.max()
            if var_cost.max() != 0:
                var_cost = var_cost / var_cost.max()
            if fix_cost.max() != 0:
                fix_cost = fix_cost / fix_cost.max()

        fig.add_trace(
            go.Scattergl(x=df.index, y=flow, name=f"{label} (flow)",
                         legendgroup=label, mode="lines", line=dict(color=color)),
            row=1, col=1
        )

        fig.add_trace(
            go.Scattergl(x=df.index, y=var_cost, name=f"{label} (var cost)",
                         legendgroup=label, mode="lines", showlegend=False,
                         line=dict(color=color)),
            row=2, col=1
        )

        fig.add_trace(
            go.Scattergl(x=df.index, y=fix_cost, name=f"{label} (fix cost)",
                         legendgroup=label, mode="lines", showlegend=False,
                         line=dict(color=color)),
            row=3, col=1
        )

        fig.add_trace(
            go.Scattergl(x=df.index, y=total_cost, name=f"{label} (total cost)",
                         legendgroup=label, mode="lines", showlegend=False,
                         line=dict(color=color)),
            row=4, col=1
        )

    if storage_content is not None:
        storage_colors = px.colors.qualitative.Dark24
        for i, storage in enumerate(storage_content.columns):
            color = storage_colors[i % len(storage_colors)]
            fig.add_trace(
                go.Scattergl(x=storage_content.index,
                             y=storage_content[storage].clip(lower=0),
                             name=f"{storage} (storage)",
                             legendgroup=f"storage_{storage}",
                             mode="lines",
                             line=dict(color=color, dash="dash")),
                row=5, col=1
            )

    fig.update_layout(
        height=900,
        title="Energy System Flows & Costs",
        hovermode="x unified"
    )

    fig.write_html(
        "plot_specific.html" if specific else "plot_total.html",
        include_plotlyjs="cdn",
        auto_open=True
    )


def get_flow_cost_breakdown(f, all_flow_dict: dict, split: bool = False) -> pd.DataFrame:
    contrib = all_flow_dict[f]["contrib"].copy()
    if contrib.empty:
        return contrib
    merged = _sum_columns_by_level(contrib, [0, 1])
    if split:
        return merged
    return _sum_columns_by_level(merged, "origin")


def plot_flow_cost_breakdown(all_flow_dict: dict, specific: bool = True,
                             filename: str = "flow_cost_breakdown.html",
                             auto_open: bool = True, min_total: float = 1.0):
    timeindex = next(iter(all_flow_dict.values()))["flow_df"].index

    breakdown = {}
    for f, rec in all_flow_dict.items():
        contrib = rec["contrib"].copy()
        if contrib.empty:
            merged = pd.DataFrame(
                0.0, index=timeindex,
                columns=pd.MultiIndex.from_arrays([[], []], names=["origin", "type"]),
            )
        else:
            merged = _sum_columns_by_level(contrib, [0, 1])
        fix = merged.xs("fix", level="type", axis=1)
        var = merged.xs("var", level="type", axis=1)

        def keep_columns(df: pd.DataFrame) -> pd.DataFrame:
            keep = df.sum(axis=0).abs() > min_total
            return df.loc[:, keep]

        fix = keep_columns(fix)
        var = keep_columns(var)
        total = pd.DataFrame(0.0, index=timeindex, columns=pd.Index([], name="part"))
        for o in fix.columns:
            total[f"{o} (fix)"] = fix[o]
        for o in var.columns:
            total[f"{o} (var)"] = var[o]

        if specific:
            flow = rec["flow_df"]["flow_v"]
            total = total.div(flow, axis=0).where(flow != 0, 0)
            fix = fix.div(flow, axis=0).where(flow != 0, 0)
            var = var.div(flow, axis=0).where(flow != 0, 0)
        breakdown[(f, "total")] = total
        breakdown[(f, "fix")] = fix
        breakdown[(f, "var")] = var

    combos = [(f, "total") for f in all_flow_dict]

    n_slots = 2 * max(len(breakdown[c].columns) for c in breakdown) + 1
    palette = px.colors.qualitative.Plotly
    hover_fmt = ".4f" if specific else ".2f"
    unit = "EUR/kWh" if specific else "EUR"

    def button_args(f, ctype):
        dfm = breakdown[(f, ctype)]
        cols = list(dfm.columns)
        bases = []
        for c in cols:
            base = c[:-6] if c.endswith(" (fix)") else (c[:-6] if c.endswith(" (var)") else c)
            if base not in bases:
                bases.append(base)
        origins = []
        for base in bases:
            for suffix in (" (fix)", " (var)"):
                c = base + suffix
                if c in cols:
                    origins.append(c)
        n = len(origins)
        x = [timeindex.to_list()] * n_slots
        y = [None] * n_slots
        names = [""] * n_slots
        stack = [None] * n_slots
        mode = ["lines"] * n_slots
        vis = [False] * n_slots
        line = [dict()] * n_slots
        fillcolor = [None] * n_slots
        legendgroup = [None] * n_slots
        showlegend = [False] * n_slots
        customdata = [None] * n_slots
        hovertemplate = [None] * n_slots
        hoverinfo = [None] * n_slots
        for i, o in enumerate(origins):
            color = dict(color=palette[i % len(palette)])
            col = dfm[o]
            y[i] = col.clip(lower=0).to_list()
            y[n + i] = col.clip(upper=0).to_list()
            names[i] = names[n + i] = str(o)
            stack[i] = "pos"
            stack[n + i] = "neg"
            mode[i] = mode[n + i] = "none"
            vis[i] = vis[n + i] = True
            line[i] = line[n + i] = color
            fillcolor[i] = fillcolor[n + i] = color["color"]
            legendgroup[i] = legendgroup[n + i] = str(o)
            showlegend[i] = True
            customdata[i] = col.to_list()
            hovertemplate[i] = f"{o}<br>%{{customdata:{hover_fmt}}} {unit}"
            hoverinfo[n + i] = "skip"
        total_i = 2 * n
        y[total_i] = dfm.sum(axis=1).to_list()
        names[total_i] = "total"
        stack[total_i] = None
        mode[total_i] = "lines"
        vis[total_i] = True
        line[total_i] = dict(color="black", width=2)
        legendgroup[total_i] = "total"
        showlegend[total_i] = True
        hovertemplate[total_i] = f"total<br>%{{y:{hover_fmt}}} {unit}"
        return dict(x=x, y=y, name=names, stackgroup=stack, mode=mode,
                    visible=vis, line=line, fillcolor=fillcolor,
                    legendgroup=legendgroup, showlegend=showlegend,
                    customdata=customdata, hovertemplate=hovertemplate,
                    hoverinfo=hoverinfo)

    buttons = []
    for f, ctype in combos:
        label = f"{f[0].label} -> {f[1].label} (total)"
        buttons.append(dict(label=label, method="update",
                            args=[button_args(f, ctype)]))

    first = button_args(*combos[0])
    fig = go.Figure()
    for s in range(n_slots):
        fig.add_trace(go.Scatter(
            x=first["x"][s], y=first["y"][s], name=first["name"][s],
            stackgroup=first["stackgroup"][s], mode=first["mode"][s],
            visible=first["visible"][s], line=first["line"][s],
            fillcolor=first["fillcolor"][s],
            legendgroup=first["legendgroup"][s],
            showlegend=first["showlegend"][s],
            customdata=first["customdata"][s],
            hovertemplate=first["hovertemplate"][s],
            hoverinfo=first["hoverinfo"][s],
        ))

    fig.update_layout(
        title="Flow Cost Breakdown",
        xaxis_title="Time",
        yaxis_title="Specific cost [EUR/kWh]" if specific else "Cost [EUR]",
        hovermode="x unified",
        legend_title_text="Contributing flows",
        margin=dict(t=150, r=350),
        legend=dict(x=1.02, y=0.98, xanchor="left", yanchor="top",
                    itemdoubleclick=False),
        updatemenus=[dict(
            active=0, buttons=buttons,
            x=1.02, y=1.15, xanchor="right", yanchor="top",
            direction="down",
        )],
    )

    fig.write_html(
        filename,
        include_plotlyjs="cdn",
        auto_open=auto_open,
        post_script=[(
            "(function(){var gd=document.querySelector('.plotly-graph-div');"
            "if(!gd)return;"
            "gd.on('plotly_legendclick',function(){"
            "setTimeout(function(){Plotly.redraw(gd);},150);});})();"
        )],
    )


def print_flow_cost_summary(all_flow_dict):
    print(f"\n{'Flow':<40} {'Avg Spec Fix':>14} {'Avg Spec Var':>14} {'Avg Spec Tot':>14} {'Tot Fix':>12} {'Tot Var':>12} {'Tot Total':>12}")
    print("-" * 122)

    for f, data in all_flow_dict.items():
        df = data["flow_df"]
        label = f"{f[0].label}->{f[1].label}"

        avg_spec_fix = df["fix_c_tot_p"].sum() / df["flow_v"].sum() if df["flow_v"].sum() > 0 else 0
        avg_spec_var = df["var_c_tot_p"].sum() / df["flow_v"].sum() if df["flow_v"].sum() > 0 else 0
        avg_spec_tot = avg_spec_fix + avg_spec_var

        tot_fix = df["fix_c_tot_p"].sum()
        tot_var = df["var_c_tot_p"].sum()
        tot_total = tot_fix + tot_var

        print(f"{label:<40} {avg_spec_fix:>14.4f} {avg_spec_var:>14.4f} {avg_spec_tot:>14.4f} {tot_fix:>12.2f} {tot_var:>12.2f} {tot_total:>12.2f}")
