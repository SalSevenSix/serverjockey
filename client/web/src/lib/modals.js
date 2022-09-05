import { openModal } from 'svelte-modals';
import ConfirmModal from '$lib/ConfirmModal.svelte';
import TextAreaModal from '$lib/TextAreaModal.svelte';


export function confirmModal(messageText, confirmCallback) {
  openModal(ConfirmModal, { message: messageText, onConfirm: confirmCallback });
}

export function textAreaModal(name, text, applyChangesCallback) {
  openModal(TextAreaModal, { contentName: name, contentText: text, onApplyChanges: applyChangesCallback });
}
