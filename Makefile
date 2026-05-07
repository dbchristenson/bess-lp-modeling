RESULTS := results.pkl

.PHONY: all model figures workbook clean

all: model figures workbook

model: $(RESULTS)

$(RESULTS): build_model.py
	uv run python build_model.py

figures: $(RESULTS) build_figures.py
	uv run python build_figures.py

workbook: $(RESULTS) build_workbook.py
	uv run python build_workbook.py

clean:
	rm -f $(RESULTS) BESS_DR_Model_Results.xlsx
	rm -rf figures/
