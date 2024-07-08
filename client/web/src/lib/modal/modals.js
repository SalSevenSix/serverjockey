import { openModal } from 'svelte-modals';
import ConfirmModal from '$lib/modal/ConfirmModal.svelte';
import TextAreaModal from '$lib/modal/TextAreaModal.svelte';


export function confirmModal(messageText, confirmCallback) {
  openModal(ConfirmModal, { message: messageText, onConfirm: confirmCallback });
}

export function confirmDangerModal(messageText, name, confirmCallback) {
  openModal(ConfirmModal, { message: messageText, confirmName: name, onConfirm: confirmCallback });
}

export function textAreaModal(name, text, saveCallback) {
  openModal(TextAreaModal, { contentName: name, contentText: text, onSave: saveCallback });
}
