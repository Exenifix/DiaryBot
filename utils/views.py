import asyncio
from enum import Enum
from typing import Any, Generic, TypeVar

import disnake


class ResponseMode(Enum):
    DELETE = 0
    EDIT = 1


class _TimeoutType:
    pass


T = TypeVar("T")
TIMEOUT = _TimeoutType()


class BaseView(disnake.ui.View):
    """
    Base View class that performs interaction check.
    """

    def __init__(self, user_id: int, *, timeout: float | None = 180.0) -> None:
        self.user_id = user_id
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.send("This button is not for you 🤭", ephemeral=True, delete_after=3)
            return False
        return True

    def disable_components(self) -> None:
        for child in self.children:
            child.disabled = True


class GenericButton(disnake.ui.Button, Generic[T]):
    """
    Generic Button to be used with ``GenericView``.
    """

    def __init__(self, return_value: T, *args: Any, **kwargs: Any) -> None:
        """
        Generic Button to be used with ``GenericView``.
        :param return_value: Value that ``GenericView.get_result()`` will return if this button was pressed
        :param args: ``disnake.ui.Button`` init args
        :param kwargs: ``disnake.ui.Button`` init kwargs
        """
        super().__init__(*args, **kwargs)
        self.return_value = return_value

    async def callback(self, interaction: disnake.MessageInteraction, /) -> None:
        view: GenericView[T] = self.view
        view.result = self.return_value
        view.inter = interaction
        view.stop()


class GenericSelectOption(disnake.SelectOption, Generic[T]):
    """
    Generic SelectOption to be used with `GenericSelect`.
    """

    def __init__(
        self,
        return_value: T,
        *,
        label: str,
        description: str | None = None,
        emoji: str | disnake.Emoji | disnake.PartialEmoji | None = None,
        default: bool = False,
    ) -> None:
        """
        Generic SelectOption to be used with ``GenericSelect``.
        :param return_value: Value that will be included if this options is selected
            to ``GenericView.get_result()`` if parent ``GenericSelect``'s ``max_value`` equals 1,
            otherwise ``GenericView.get_result()`` result on this option select.
        :param label: Label of the option.
        :param description: Description of the option.
        :param emoji: Emoji of the option.
        :param default: Whether this option should be enabled by default.
        """
        super().__init__(label=label, description=description, emoji=emoji, default=default)
        self.return_value = return_value


class GenericSelect(disnake.ui.StringSelect, Generic[T]):
    """
    Generic Select to be used with ``GenericView``.
    """

    def __init__(
        self,
        *,
        options: list[GenericSelectOption[T]],
        custom_id: str = disnake.utils.MISSING,
        placeholder: str | None = None,
        min_values: int = 1,
        max_values: int | None = None,
        disabled: bool = False,
        row: int | None = None,
    ) -> None:
        """
        Generic Select to be used with ``GenericView``.
        :param options: List of ``GenericSelectOption`` with specified return values.
        :param custom_id: Custom ID of component.
        :param placeholder: Placeholder on no options selected.
        :param min_values: Minimum possible amount of options to select. Defaults to ``1``.
        :param max_values: Maximum possible amount of options to select. **Defaults to amount of options!**
        :param disabled: Whether this component is disabled.
        :param row: Row number to put this on.
        """
        self._mapping: dict[str, T] = {}
        for i, option in enumerate(options):
            si = str(i)
            option.value = si
            self._mapping[si] = option.return_value

        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values or len(options),
            options=options,
            disabled=disabled,
            row=row,
        )

    @property
    def values(self) -> list[T]:
        return list(map(self._mapping.get, super().values))

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view: GenericView = self.view
        view.result = self.values[0] if self.max_values == self.min_values == 1 else self.values
        view.inter = interaction
        view.stop()


class GenericChannelSelect(disnake.ui.ChannelSelect):
    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        view: GenericView = self.view
        view.result = self.values[0] if self.max_values == self.min_values == 1 else self.values
        view.inter = interaction
        view.stop()


class GenericView(BaseView, Generic[T]):
    """
    Generic View class for obtaining interacted components in-place.
    """

    result: T | list[T] | _TimeoutType
    inter: disnake.MessageInteraction

    def __init__(
        self,
        user_id: int,
        components: list[GenericButton[T] | GenericSelect[T] | GenericChannelSelect],
        *,
        timeout: float | None = 180.0,
    ) -> None:
        """
        Generic View class for obtaining interacted components in-place.
        :param user_id: User ID to restrict the view to.
        :param components: List of ``GenericButton`` and/or ``GenericSelect`` to include into view.
        :param timeout: When the view should time out.
        """
        super().__init__(user_id, timeout=timeout)
        self.result = TIMEOUT
        for item in components:
            self.add_item(item)

    async def get_result(
        self, inter: disnake.Interaction | None = None, /, response_mode: ResponseMode = ResponseMode.DELETE
    ) -> tuple[T | list[T], disnake.MessageInteraction]:
        """
        Get ``return_value``(s) of interacted component(s).

        :param inter: If provided, deletes/edits the original interaction response
        :param response_mode: If DELETE, deletes response, if EDIT, disables all components and updates
        :return: Component's ``return_value``. If one of components is ``GenericSelect`` and its
            ``max_value`` greater than 1, return list of ``return_value``s of selected options.
        """
        await self.wait()
        if inter is not None:
            try:
                if response_mode == ResponseMode.DELETE:
                    await inter.delete_original_response()
                elif response_mode == ResponseMode.EDIT:
                    self.disable_components()
                    await inter.edit_original_response(view=self)
            except disnake.HTTPException:
                pass
        if self.result is TIMEOUT:
            raise asyncio.TimeoutError()
        return self.result, self.inter

    async def on_timeout(self) -> None:
        self.result = TIMEOUT
        self.stop()


class ConfirmationView(GenericView):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            user_id,
            [
                GenericButton(True, label="Confirm", style=disnake.ButtonStyle.green),
                GenericButton(False, label="Cancel", style=disnake.ButtonStyle.red),
            ],
        )


class Modal(disnake.ui.Modal):
    """
    Modal class that waits for user to fill modal out then returns results.
    """

    _fut: asyncio.Future
    _inter: disnake.ModalInteraction

    async def on_timeout(self) -> None:
        self._fut.set_result(True)

    async def callback(self, interaction: disnake.ModalInteraction, /) -> None:
        # noinspection PyProtectedMember
        interaction._state._modal_store.remove_modal(interaction.author.id, interaction.custom_id)
        self._inter = interaction
        self._fut.set_result(False)

    async def wait(self) -> disnake.ModalInteraction:
        """
        Waits for user to fill modal out and returns resulting interaction.
        :return: Resulting ``ModalInteraction``.
        :raise asyncio.TimeoutError: Modal was timed out.
        """
        self._fut = asyncio.shield(asyncio.get_event_loop().create_future())
        if await self._fut:
            raise asyncio.TimeoutError()
        return self._inter
