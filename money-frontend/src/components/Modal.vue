<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isVisible" class="fixed inset-0 z-50 overflow-y-auto" @click.self="close" role="dialog" aria-modal="true">
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
          <!-- Background overlay -->
          <div class="fixed inset-0 transition-opacity bg-gray-900 bg-opacity-75" aria-hidden="true"></div>
          
          <!-- Center modal content -->
          <div class="inline-block align-bottom bg-gray-800 border border-gray-700 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
            <!-- Close button -->
            <button 
              @click="close" 
              class="absolute top-3 right-3 text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-full p-1"
              aria-label="Close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            <!-- Modal content -->
            <div class="p-6">
              <slot></slot>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { onMounted, onBeforeUnmount, watch } from 'vue';

export default {
  name: 'Modal',
  props: {
    isVisible: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['close'],
  setup(props, { emit }) {
    // Handle escape key press to close modal
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && props.isVisible) {
        emit('close');
      }
    };
    
    // Add event listener for escape key
    onMounted(() => {
      document.addEventListener('keydown', handleEscapeKey);
    });
    
    // Remove event listener when component unmounts
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleEscapeKey);
    });
    
    // Lock body scroll when modal is open
    watch(() => props.isVisible, (isVisible) => {
      if (isVisible) {
        document.body.classList.add('overflow-hidden');
      } else {
        document.body.classList.remove('overflow-hidden');
      }
    }, { immediate: true });
    
    const close = () => {
      emit('close');
    };
    
    return {
      close,
    };
  },
};
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .inline-block,
.modal-leave-to .inline-block {
  transform: scale(0.9);
  opacity: 0;
}
</style>