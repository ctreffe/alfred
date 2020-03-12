# alfred v1.0

## Breaking changes

### New Names
- `Page` replaces `WebCompositeQuestion`
- `Section` replaces `QuestionGroup`
- `SegmentedSection` replaces `SegmentedQG`
- `HeadOpenSection` repladces `HeadOpenQG`

### `generate_experirment` and experiment metadata

### File import


## New Features

### Tidier `script.py` style

### `.append()`
- `Page.append()`
- `Section.append()`
- `Experiment.append()`

### Other new features
- `Page.on_showing()`
- `Page.get_page_data()`
- `Experiment.change_final_page()`

## Experimental Features

## Deprecated
- `Page.on_showing_widget()` is replaced by `Page.on_showing()`.
- `Page.on_hiding_widget()` is replaced by `Page.on_hiding()`.
- `Page.add_element()`, in the previous version named `WebCompositeQuestion.addElement()`, is replaced by `Page.append()`.
- `Page.add_elements()`, in the previous version named `WebCompositeQuestion.addElements()`, is replaced by `Page.append()`.
- `Section.append_item()`, in the previous version named `QuestionGroup.appendItem()`, is replaced by `Section.append()`.
- `Section.append_items()`, in the previous version named `QuestionGroup.appendItems()`, is replaced by `Section.append()`.
- `Experiment.page_controller.append_item()`, in the previous version named `Experiment.questionController.appendItem()`, is replaced by `Experiment.append()`.
- `Experiment.page_controller.append_items()`, in the previous version named `Experiment.questionController.appendItems()`, is replaced by `Experiment.append()`.

## Bug fixes and minor changes