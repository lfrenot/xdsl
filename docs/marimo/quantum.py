import marimo

__generated_with = "0.7.5"
app = marimo.App()


@app.cell
def __():
    import marimo as mo

    mo.md("""
    # Quantum xDSL demo
    """
    )
    return mo,


@app.cell
def __():
    from xdsl.builder import Builder
    from xdsl.dialects.builtin import ModuleOp
    from xdsl.dialects import qref, qssa
    from xdsl.dialects.quantum import AngleAttr
    from xdsl.passes import PipelinePass
    return AngleAttr, Builder, ModuleOp, PipelinePass, qref, qssa


@app.cell
def __(ModuleOp, mo):
    import html as htmllib

    def html(module: ModuleOp) -> mo.Html:
        return f"""\
        <small><code style="white-space: pre-wrap;">{htmllib.escape(str(module))}</code></small>
        """
        # return mo.as_html(str(module))
    return html, htmllib


@app.cell
def __(AngleAttr, Builder, ModuleOp, html, mo, qref):
    module = ModuleOp(())
    builder = Builder.at_end(module.body.first_block)

    a, b = builder.insert(qref.QRefAllocOp(2)).results

    builder.insert(qref.HGateOp(b))
    builder.insert(qref.RZGateOp(AngleAttr.from_fraction(1,2), b))
    builder.insert(qref.CNotGateOp(a,b))
    builder.insert(qref.HGateOp(b))
    builder.insert(qref.RZGateOp(AngleAttr.from_fraction(1,2), b))
    builder.insert(qref.HGateOp(b))
    builder.insert(qref.CNotGateOp(a,b))


    mo.md(f"""
    We can build a simple sequence of gates.

    This can then be displayed in an familiar syntax:

    {html(module)}
    """)
    return a, b, builder, module


@app.cell
def __():
    from xdsl.context import MLContext
    from xdsl.tools.command_line_tool import get_all_dialects
    ctx = MLContext()

    for dialect_name, dialect_factory in get_all_dialects().items():
        ctx.register_dialect(dialect_name, dialect_factory)
    return MLContext, ctx, dialect_factory, dialect_name, get_all_dialects


@app.cell
def __(ctx, html, mo, module):
    from xdsl.transforms.convert_qref_to_qssa import ConvertQRefToQssa

    ConvertQRefToQssa().apply(ctx, module)

    mo.md(f"""
    We can convert this to ssa form to get:

    {html(module)}

    This allows us to perform local pattern rewrites
    """)
    return ConvertQRefToQssa,


@app.cell
def __(ModuleOp, ModulePass, PipelinePass, ctx, html, mo):
    from collections import Counter

    def spec_str(p: ModulePass) -> str:
        if isinstance(p, PipelinePass):
            return ",".join(str(c.pipeline_pass_spec()) for c in p.passes)
        else:
            return str(p.pipeline_pass_spec())

    def pipeline_accordion(
        passes: tuple[tuple[mo.Html, ModulePass], ...], module: ModuleOp
    ) -> tuple[ModuleOp, mo.Html]:
        res = module.clone()
        d = {}
        total_key_count = Counter(spec_str(p) for _, p in passes)
        d_key_count = Counter()
        for text, p in passes:
            p.apply(ctx, res)
            spec = spec_str(p)
            d_key_count[spec] += 1
            if total_key_count[spec] != 1:
                header = f"{spec} ({d_key_count[spec]})"
            else:
                header = spec
            html_res = html(res)
            d[header] = mo.vstack(
                (
                    text,
                    mo.md(html_res),
                )
            )
        return (res, mo.accordion(d))
    return Counter, pipeline_accordion, spec_str


@app.cell
def __(PipelinePass, module, pipeline_accordion):
    from xdsl.transforms.qssa_rewrites import ReduceHadamardPass, GateCancellation


    simpl = PipelinePass(
        [
            ReduceHadamardPass(),
            GateCancellation(),
        ]
    )

    simpl_module, simpl_accordion = pipeline_accordion(
        tuple(("", p) for p in simpl.passes), module
    )

    simpl_accordion
    return (
        GateCancellation,
        ReduceHadamardPass,
        simpl,
        simpl_accordion,
        simpl_module,
    )


@app.cell
def __(ctx, html, mo, module, simpl_module):
    from xdsl.transforms.convert_qssa_to_qref import ConvertQssaToQRef

    ConvertQssaToQRef().apply(ctx, module)
    ConvertQssaToQRef().apply(ctx, simpl_module)

    mo.md(f"""
    This can be roundtripped back to a reference semantics form:

    {html(module)}

    or we can convert our simplified module:

    {html(simpl_module)}
    """)
    return ConvertQssaToQRef,


if __name__ == "__main__":
    app.run()
