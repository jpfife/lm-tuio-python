"""Actively Loaded Models display widget data structures and classes."""

from collections.abc import Callable
from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import DescendantBlur, DescendantFocus
from textual.widgets import Collapsible, Label, SelectionList, Static
from textual.widgets.selection_list import Selection

from lm_tuio import events
from lm_tuio.config import KeymapManager
from lm_tuio.models import ModelInfo, format_bytes


@dataclass
class LoadedInstance:
    """Running instance representation of a model."""

    instance_id: str
    display_label: str
    model_info: ModelInfo


@dataclass
class LoadedModelGroup:
    """Base model group with running instances."""

    base_model_key: str
    display_name: str
    instances: list[LoadedInstance]


class LoadedModels(Static):
    """Collapsible view of running instances."""

    BINDINGS = KeymapManager.get_bindings("loaded_models")

    def __init__(
        self,
        post_unload_model_request_callback: Callable[[list[str]]],
        post_highlighted_model_callback: Callable[[ModelInfo | None]],
        *args,
        **kwargs,
    ) -> None:
        self._groups: dict[str, LoadedModelGroup] = {}
        self._instance_map: dict[str, LoadedInstance] = {}
        self.current_filter: str = ""

        # Post message callback for event bus
        self.post_unload_model_request = post_unload_model_request_callback
        self.post_highlighted_model = post_highlighted_model_callback
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        self.total_model_mem: Label = Label(
            "Total Model Memory Usage: ", id="loaded-models-total-mem"
        )
        self.total_model_mem_val: Label = Label(
            "0.00 MB", id="loaded-models-total-mem-val"
        )
        self.loaded_models_scroll: VerticalScroll = VerticalScroll(
            id="loaded-models-scroll"
        )

        with Horizontal(id="loaded-models-total-mem-header"):
            with Vertical(classes="vert-mem-header"):
                yield self.total_model_mem
            with Vertical(classes="vert-mem-header"):
                yield self.total_model_mem_val

        yield self.loaded_models_scroll

    def load_model_groups(self, models: list[ModelInfo]) -> None:
        """Populates model groups with loaded base models/instances."""

        groups: list[LoadedModelGroup] = []

        for model in models:
            if not model.loaded_instances:
                continue

            ui_instances: list[LoadedInstance] = []
            for inst in model.loaded_instances:
                ctx_str = (
                    f"{format_bytes(inst.config.context_length)}"
                    if inst.config.context_length
                    else "?"
                )

                if len(inst.id) > 27:
                    label_parts = [f"...{inst.id[-24:]}"]
                else:
                    label_parts = [f"{inst.id}"]
                label_parts.append(f"ctx: {ctx_str}")
                display_label = " | ".join(label_parts)

                ui_instances.append(
                    LoadedInstance(
                        instance_id=inst.id,
                        display_label=display_label,
                        model_info=model,
                    )
                )

            groups.append(
                LoadedModelGroup(
                    base_model_key=model.key,
                    display_name=model.display_name,
                    instances=ui_instances,
                )
            )

        self._groups = {g.base_model_key: g for g in groups}
        self._instance_map.clear()

        for group in groups:
            for inst in group.instances:
                self._instance_map[inst.instance_id] = inst

        # Get total model memory
        total_bytes: int = sum(
            inst.model_info.size_bytes for inst in self._instance_map.values()
        )
        self.total_model_mem_val.update(f"{format_bytes(total_bytes)}")

        self.refresh_groups()

    def clear_model_list(self) -> None:
        """Clear model instance listings."""
        self.total_model_mem_val.update("0.00 MB")
        self._groups.clear()
        self._instance_map.clear()

    def refresh_groups(self) -> None:
        """Rebuilds collapsible group listing based on current filter."""
        self.loaded_models_scroll.remove_children()
        self.mount(self.total_model_mem, self.total_model_mem_val)

        term = self.current_filter.lower()
        has_visible_items = False

        for group in self._groups.values():
            base_model_matches = term in group.display_name.lower()
            instance_matches = [
                inst
                for inst in group.instances
                if base_model_matches
                or term in inst.display_label.lower()
                or term in inst.instance_id.lower()
                or term in inst.model_info.publisher.lower()
                or term in inst.model_info.key.lower()
                or (
                    inst.model_info.architecture
                    and term in inst.model_info.architecture.lower()
                )
                or (
                    inst.model_info.quantization
                    and term in inst.model_info.quantization.name.lower()
                )
            ]

            if not instance_matches:
                continue

            has_visible_items = True

            selections = [
                Selection(inst.display_label, inst.instance_id, initial_state=False)
                for inst in instance_matches
            ]

            collapsible = Collapsible(
                SelectionList(
                    *selections,
                ),
                title=f"{group.display_name} ({len(instance_matches)})",
                collapsed=False,
            )
            self.loaded_models_scroll.mount(collapsible)

        if not has_visible_items:
            if self._instance_map:
                self.loaded_models_scroll.mount(
                    Label("No filter match", classes="section-title")
                )
            else:
                self.loaded_models_scroll.mount(
                    Label("No models loaded", classes="section-title")
                )

    def apply_filter(self, search_term: str) -> None:
        """Apply Dashboard search filter term to groups/instances."""
        self.current_filter = search_term
        self.refresh_groups()

    # ======= ACTIONS =======

    def action_toggle_group(self) -> None:
        """Toggles all checkboxes in the currently focused SelectionList."""
        focused = self.app.focused
        if isinstance(focused, SelectionList):
            all_selected = len(focused.selected) == len(focused.options)
            if all_selected:
                focused.deselect_all()
            else:
                focused.select_all()

    def action_unload_selected(self) -> None:
        """Gathers all checkboxes across all collapsible groups and fires unload."""
        selected_ids: list[str] = []
        for sel_list in self.query(SelectionList):
            selected_ids.extend(sel_list.selected)

        if selected_ids:
            self.post_message(events.UnloadInstancesRequested(selected_ids))
        else:
            self.post_message(
                events.ActionLogUpdate("No instances checked for unloading", "warn")
            )

    def action_unload_all(self) -> None:
        """Sends all currently loaded model instances for unload."""
        all_ids = list(self._instance_map.keys())
        if all_ids:
            self.post_message(events.UnloadInstancesRequested(all_ids))

    def action_select_up(self) -> None:
        if isinstance(self.app.focused, SelectionList):
            self.app.focused.action_cursor_up()

    def action_select_down(self) -> None:
        if isinstance(self.app.focused, SelectionList):
            self.app.focused.action_cursor_down()

    # ========== EVENTS ==========

    @on(SelectionList.SelectionHighlighted)
    def handle_instance_highlight(
        self, event: SelectionList.SelectionHighlighted
    ) -> None:
        """Updates ContextPane when cursor moves over a specific loaded instance."""
        if not self.has_focus_within:
            return

        inst = self._instance_map.get(event.selection.value)
        if inst:
            self.post_message(self.post_highlighted_model(inst.model_info))

    @on(DescendantFocus)
    def on_list_focus(self, event: DescendantFocus) -> None:
        """Restore cursor and re-emit selection when table gains focus."""
        focused = event.widget
        if not isinstance(focused, SelectionList):
            return

        if focused.highlighted is None:
            if focused.option_count > 0:
                focused.highlighted = 0  # Default to top item if no highlight
            else:
                self.post_message(self.post_highlighted_model(None))
                return

        option = focused.get_option_at_index(focused.highlighted)
        inst = self._instance_map.get(option.value)
        if inst:
            self.post_message(self.post_highlighted_model(inst.model_info))
        else:
            self.post_message(self.post_highlighted_model(None))

    @on(DescendantBlur)
    def on_list_blur(self) -> None:
        self.show_cursor = False
