<template>
  <Transition name="modal-fade">
    <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div class="flex items-center justify-center min-h-screen p-4">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black bg-opacity-70 transition-opacity" @click="closeOnBackdrop && close()"></div>
        
        <!-- Modal panel -->
        <div 
          class="bg-gray-800 rounded-lg shadow-xl transform transition-all max-w-md w-full overflow-hidden border border-gray-700"
          :class="[sizeClass, {'md:max-w-4xl': size === 'large', 'md:max-w-2xl': size === 'medium'}]"
        >
          <!-- Header -->
          <div class="px-6 py-4 bg-gray-900 flex justify-between items-center border-b border-gray-700">
            <h3 class="text-xl font-bold text-purple-400" id="modal-title">
              {{ title }}
            </h3>
            <button 
              @click="close" 
              class="text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 rounded"
              aria-label="Close"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <!-- Content -->
          <div class="px-6 py-4">
            <slot></slot>
          </div>
          
          <!-- Footer (optional) -->
          <div v-if="$slots.footer" class="px-6 py-3 bg-gray-900 border-t border-gray-700">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';

export default {
  name: 'Modal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: 'Modal Title'
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large'].includes(value)
    },
    closeOnBackdrop: {
      type: Boolean,
      default: true
    }
  },
  emits: ['close', 'update:isOpen'],
  setup(props, { emit }) {
    const close = () => {
      emit('update:isOpen', false);
      emit('close');
    };
    
    // Handle ESC key to close modal
    const handleEscKey = (event) => {
      if (event.key === 'Escape' && props.isOpen) {
        close();
      }
    };
    
    // Add/remove event listeners
    onMounted(() => {
      document.addEventListener('keydown', handleEscKey);
    });
    
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleEscKey);
    });
    
    // Prevent body scroll when modal is open
    watch(() => props.isOpen, (isOpen) => {
      if (isOpen) {
        document.body.classList.add('overflow-hidden');
      } else {
        document.body.classList.remove('overflow-hidden');
      }
    });
    
    // Compute size class based on size prop
    const sizeClass = computed(() => {
      return {
        'sm:max-w-sm': props.size === 'small',
        'sm:max-w-md': props.size === 'medium',
        'sm:max-w-lg': props.size === 'large'
      };
    });
    
    return {
      close,
      sizeClass
    };
  }
};
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>