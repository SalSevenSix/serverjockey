import { openModal } from 'svelte-modals';
import ConfirmModal from '$lib/ConfirmModal.svelte';


export function confirmModal(messageText, confirmCallback) {
  openModal(ConfirmModal, { message: messageText, onConfirm: confirmCallback });
}
