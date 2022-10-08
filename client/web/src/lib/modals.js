import { openModal } from 'svelte-modals';
import LoginModal from '$lib/LoginModal.svelte';
import ConfirmModal from '$lib/ConfirmModal.svelte';
import TextAreaModal from '$lib/TextAreaModal.svelte';


export function loginModal() {
  openModal(LoginModal);
}

export function confirmModal(messageText, confirmCallback) {
  openModal(ConfirmModal, { message: messageText, onConfirm: confirmCallback });
}

export function confirmDangerModal(messageText, name, confirmCallback) {
  openModal(ConfirmModal, { message: messageText, confirmName: name, onConfirm: confirmCallback });
}

export function textAreaModal(name, text, applyChangesCallback) {
  openModal(TextAreaModal, { contentName: name, contentText: text, onApplyChanges: applyChangesCallback });
}
