# Interactive Marimo Notebooks for rust-quant

This directory contains interactive [Marimo](https://marimo.io/) notebook versions of the rust-quant examples. Explore option pricing, yield curves, and Monte Carlo simulation with live, reactive visualizations.

## What is Marimo?

[Marimo](https://marimo.io/) is a next-generation reactive Python notebook that runs as an interactive web application. It's designed to solve common problems with traditional notebooks like Jupyter.

### Key Features

**🔄 Reactive Execution**
- Cells automatically re-run when their dependencies change
- No stale outputs - always shows current state
- Real-time updates as you modify code

**📊 Interactive UI Elements**
- Built-in sliders, dropdowns, tables, and charts
- Parameter exploration without code changes
- Instant visual feedback

**🔒 Reproducible**
- No hidden state - deterministic execution order
- Every run produces the same results
- Dependencies are explicit and tracked

**🗂️ Git-Friendly**
- Notebooks are pure Python files (`.py`, not `.ipynb`)
- Clean diffs in version control
- No JSON merge conflicts
- Easy code review

**🎨 Modern Web UI**
- Beautiful, responsive interface
- Dark mode support
- Export to static HTML
- Share as standalone apps


## Getting Started

### Installation

First, install Marimo:

```bash
# Install marimo in your rust-quant environment
uv pip install marimo

# Or globally
pip install marimo
# or
pipx install marimo
```

### Running Notebooks

Marimo offers three modes for running notebooks:

#### 1. Interactive App Mode (Read-Only)

Run a notebook as an interactive web application:

```bash
marimo run marimo_examples/01_basic_single_option.py
```

- Opens in your browser at `http://localhost:2718`
- Interactive UI elements (sliders, dropdowns)
- Read-only - cannot edit code
- Perfect for presentations or sharing with non-technical users
- Press `Ctrl+C` to stop

#### 2. Edit Mode (Development)

Edit and run the notebook interactively:

```bash
marimo edit marimo_examples/01_basic_single_option.py
```

- Opens in your browser with code editing enabled
- Modify code and see results update in real-time
- Add new cells, rearrange, delete
- Save changes directly
- Auto-format on save

#### 3. Headless Mode (CLI)

Run all cells and print output to terminal:

```bash
marimo run --headless marimo_examples/01_basic_single_option.py
```

- No browser window
- Output goes to stdout
- Useful for automation, CI/CD, or quick checks
- Faster than opening browser

## Available Notebooks

| Notebook | Description |
|----------|-------------|
| `01_basic_single_option.py` | Basic European option pricing and Greeks |
| `02_multiple_options_vectorized.py` | Vectorized pricing for multiple options |
| `03_performance_benchmark.py` | Performance benchmarking |
| `04_dividend_yield_example.py` | Options with dividend yields |
| `05_american_options_example.py` | American option pricing |
| `06_american_batch_pricing.py` | Batch pricing for American options |
| `07_zero_coupon_curve.py` | Zero-coupon curve construction |
| `08_monte_carlo_paths.py` | Monte Carlo path generation |

## Comparison: Marimo vs Regular Python Scripts

The `examples/` directory contains traditional Python scripts, while `marimo_examples/` contains interactive notebooks. Here's when to use each:

### Regular Python Scripts (`examples/`)

**Best for:**
- ✅ Running from command line
- ✅ Automation and scripting
- ✅ CI/CD pipelines
- ✅ Quick one-off calculations
- ✅ Learning the API sequentially

**Characteristics:**
- Print-based output to console
- Sequential execution
- Simple to run: `uv run python examples/01_basic_single_option.py`
- Easy to integrate into larger scripts

### Marimo Notebooks (`marimo_examples/`)

**Best for:**
- ✅ Interactive exploration and experimentation
- ✅ Parameter sensitivity analysis
- ✅ Visualizing results with charts/tables
- ✅ Presenting to non-technical stakeholders
- ✅ Teaching and demonstrations

**Advantages over scripts:**
- **Interactive parameters**: Sliders and dropdowns instead of hard-coded values
- **Visual output**: Charts, tables, formatted markdown
- **Real-time updates**: Change a parameter, see all results update instantly
- **Cell-based**: Each section is independent and can be rerun
- **Reactive**: Dependencies are tracked automatically
- **Shareable**: Export to HTML or deploy as web app

### Side-by-Side Comparison

| Feature | Python Scripts | Marimo Notebooks |
|---------|---------------|------------------|
| Output | Console text | Visual (charts, tables, markdown) |
| Parameters | Hard-coded | Interactive (sliders, inputs) |
| Execution | Sequential | Reactive (auto-updates) |
| Sharing | Source code | HTML export, web app |
| Editing | Text editor | Browser-based |
| Learning curve | None | Minimal |
| Best for | Automation | Exploration |

## Example Usage

### Interactive Parameter Exploration

In the Marimo notebooks, you can easily modify parameters:

```python
# Original fixed parameters
spot = 100.0
strike = 105.0

# In Marimo, make them interactive
spot = mo.ui.slider(80, 120, value=100, label="Spot Price")
strike = mo.ui.slider(80, 120, value=105, label="Strike Price")
```

Now moving the sliders instantly recalculates all dependent values!

## Tips and Best Practices

### For Beginners

1. **Start with edit mode**: `marimo edit marimo_examples/01_basic_single_option.py`
   - See code and output side-by-side
   - Experiment with changing values
   - Learn by doing

2. **Use the UI elements**:
   - Sliders for continuous parameters (spot price, volatility)
   - Dropdowns for discrete choices (call vs put)
   - Number inputs for precise values

3. **Follow the reactive flow**:
   - Notice how changing one cell updates dependent cells
   - No need to "Run All" - everything stays in sync
   - Impossible to get stale results

### For Advanced Users

1. **Create custom visualizations**:
   ```python
   import altair as alt
   chart = alt.Chart(data).mark_line().encode(x='strike', y='price')
   mo.ui.altair_chart(chart)
   ```

2. **Build interactive dashboards**:
   - Combine multiple UI elements
   - Create parameter grids
   - Link charts and tables

3. **Export and share**:
   ```bash
   # Export to static HTML
   marimo export html marimo_examples/01_basic_single_option.py > report.html

   # Deploy as web app (read-only)
   marimo run marimo_examples/01_basic_single_option.py --host 0.0.0.0 --port 8080
   ```

4. **Use reactive patterns**:
   - Define UI elements in one cell
   - Reference them in other cells via `.value`
   - Let Marimo handle dependencies automatically

### Performance Tips

1. **Expensive computations**: Use `@functools.cache` for expensive calculations
2. **Large datasets**: Marimo handles lazy evaluation efficiently
3. **Plotting**: Marimo integrates with matplotlib, plotly, altair, and more

## Documentation

- [Marimo Documentation](https://docs.marimo.io/)
- [Marimo Tutorial](https://docs.marimo.io/getting_started/tutorial.html)
- [rust-quant Documentation](https://github.com/yourusername/rust-quant)

## Converting Your Own Examples

To convert a Python script to a Marimo notebook:

1. Split the script into logical sections (imports, setup, calculations, results)
2. Each section becomes an `@app.cell` decorated function
3. Return variables that other cells need to use
4. Use `mo.md()` for documentation and `mo.ui.*` for interactive elements

Example structure:

```python
import marimo

app = marimo.App(width="medium")

@app.cell
def _():
    import marimo as mo
    from rust_quant import EuroCallOption
    return EuroCallOption, mo

@app.cell
def _(EuroCallOption, mo):
    call = EuroCallOption(100.0, 105.0, 1.0, 0.05, 0.2)
    mo.md(f"Option Price: ${call.price():.4f}")
    return call,

if __name__ == "__main__":
    app.run()
```

## Common Questions

**Q: Can I convert my own Python scripts to Marimo notebooks?**

A: Yes! Marimo can convert existing Python scripts or Jupyter notebooks:

```bash
# Convert Python script to Marimo notebook
marimo convert your_script.py > marimo_version.py

# Convert Jupyter notebook to Marimo
marimo convert your_notebook.ipynb > marimo_version.py
```

**Q: Do Marimo notebooks work offline?**

A: Yes, Marimo runs entirely locally. No internet connection required.

**Q: Can I use Marimo notebooks in production?**

A: Yes! You can:
- Deploy as web apps with `marimo run`
- Export to static HTML for reports
- Run headless in CI/CD pipelines
- Embed in larger Python applications

**Q: What's the difference between Marimo and Jupyter?**

A: Key differences:
- **Reactivity**: Marimo automatically updates dependent cells
- **No hidden state**: Execution order is deterministic
- **Pure Python**: Notebooks are regular `.py` files, not JSON
- **Built-in UI elements**: Sliders, dropdowns, etc. without widgets
- **Git-friendly**: Clean diffs, no merge conflicts

**Q: How do I share a Marimo notebook with someone who doesn't have Marimo installed?**

A: Export to HTML:

```bash
marimo export html marimo_examples/01_basic_single_option.py > report.html
```

The HTML file is self-contained and can be opened in any browser.

## Support and Resources

### For Marimo Questions
- **Documentation**: [https://docs.marimo.io/](https://docs.marimo.io/)
- **GitHub**: [https://github.com/marimo-team/marimo](https://github.com/marimo-team/marimo)
- **Discord**: Join the [Marimo Discord](https://discord.gg/JE7nhX6mD8)
- **Tutorials**: [https://docs.marimo.io/getting_started/tutorial.html](https://docs.marimo.io/getting_started/tutorial.html)

### For rust-quant Questions
- **Documentation**: [README.md](../README.md), [ARCHITECTURE.md](../ARCHITECTURE.md)
- **GitHub Issues**: [https://github.com/aedan-chiari/rust-quant/issues](https://github.com/aedan-chiari/rust-quant/issues)
- **Discussions**: [https://github.com/aedan-chiari/rust-quant/discussions](https://github.com/aedan-chiari/rust-quant/discussions)

## Next Steps

1. **Install Marimo**: `uv pip install marimo`
2. **Start with basics**: `marimo edit marimo_examples/01_basic_single_option.py`
3. **Experiment**: Modify parameters, add cells, create visualizations
4. **Build your own**: Convert your scripts or create new notebooks
5. **Share**: Export to HTML or deploy as web apps

Happy exploring rust-quant interactively! 🚀
