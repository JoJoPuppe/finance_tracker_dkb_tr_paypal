<template>
  <div class="relative w-full">
    <!-- Select container with search input -->
    <div 
      class="w-full relative flex items-center bg-gray-700 border border-gray-600 rounded-md transition-all"
      :class="{'ring-2 ring-purple-400': isOpen}"
      @click="toggleDropdown"
    >
      <!-- Selected value display -->
      <div class="flex-grow px-3 py-2 flex items-center justify-between">
        <div class="text-white overflow-hidden text-ellipsis whitespace-nowrap">
          {{ displayValue }}
        </div>
        <svg 
          class="w-5 h-5 text-gray-400 transition-transform"
          :class="{'transform rotate-180': isOpen}"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
        </svg>
      </div>
    </div>

    <!-- Dropdown menu with search and options -->
    <div 
      v-if="isOpen" 
      class="absolute z-50 mt-1 w-full bg-gray-800 border border-gray-600 rounded-md shadow-lg max-h-60 overflow-hidden"
      v-click-outside="closeDropdown"
    >
      <!-- Search input -->
      <div class="sticky top-0 bg-gray-800 p-2 border-b border-gray-600">
        <div class="relative">
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            class="w-full bg-gray-700 border border-gray-600 rounded-md pl-10 pr-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-purple-400"
            placeholder="Search..."
            @click.stop
          />
          <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
          </div>
          <div v-if="searchQuery" class="absolute inset-y-0 right-0 flex items-center pr-3">
            <button 
              @click.stop="clearSearch" 
              class="text-gray-400 hover:text-white focus:outline-none"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Options list with scroll -->
      <div class="overflow-y-auto max-h-48">
        <div 
          v-if="filteredOptions.length === 0" 
          class="p-4 text-center text-gray-400"
        >
          No options found
        </div>
        <div 
          v-for="option in filteredOptions" 
          :key="option.value"
          class="px-4 py-2 hover:bg-gray-700 cursor-pointer text-white"
          :class="{'bg-purple-900 bg-opacity-30': option.value === modelValue}"
          @click.stop="selectOption(option.value)"
        >
          {{ option.label }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick, watch } from 'vue';

export default {
  name: 'SearchableSelect',
  
  props: {
    options: {
      type: Array,
      required: true,
      // Each option should be { value: any, label: string }
    },
    modelValue: {
      type: [String, Number],
      required: true
    },
    placeholder: {
      type: String,
      default: 'Select an option'
    }
  },
  
  emits: ['update:modelValue'],
  
  setup(props, { emit }) {
    const isOpen = ref(false);
    const searchQuery = ref('');
    const searchInput = ref(null);
    
    // Get the display value based on the selected value
    const displayValue = computed(() => {
      if (!props.modelValue) return props.placeholder;
      
      const selectedOption = props.options.find(opt => opt.value === props.modelValue);
      return selectedOption ? selectedOption.label : props.placeholder;
    });
    
    // Filter options based on search query
    const filteredOptions = computed(() => {
      if (!searchQuery.value) return props.options;
      
      const query = searchQuery.value.toLowerCase();
      return props.options.filter(option => 
        option.label.toLowerCase().includes(query)
      );
    });
    
    // Toggle dropdown
    const toggleDropdown = () => {
      isOpen.value = !isOpen.value;
      
      if (isOpen.value) {
        nextTick(() => {
          if (searchInput.value) {
            searchInput.value.focus();
          }
        });
      }
    };
    
    // Close dropdown
    const closeDropdown = () => {
      isOpen.value = false;
      searchQuery.value = '';
    };
    
    // Clear search
    const clearSearch = () => {
      searchQuery.value = '';
      nextTick(() => {
        if (searchInput.value) {
          searchInput.value.focus();
        }
      });
    };
    
    // Select option
    const selectOption = (value) => {
      emit('update:modelValue', value);
      closeDropdown();
    };
    
    // Directive for click outside
    const clickOutside = {
      mounted(el, binding) {
        el.clickOutsideEvent = (event) => {
          if (!(el === event.target || el.contains(event.target))) {
            binding.value();
          }
        };
        document.addEventListener('click', el.clickOutsideEvent);
      },
      unmounted(el) {
        document.removeEventListener('click', el.clickOutsideEvent);
      },
    };
    
    return {
      isOpen,
      searchQuery,
      searchInput,
      displayValue,
      filteredOptions,
      toggleDropdown,
      closeDropdown,
      clearSearch,
      selectOption
    };
  },
  
  directives: {
    'click-outside': {
      mounted(el, binding) {
        el.clickOutsideEvent = (event) => {
          if (!(el === event.target || el.contains(event.target))) {
            binding.value();
          }
        };
        document.addEventListener('click', el.clickOutsideEvent);
      },
      unmounted(el) {
        document.removeEventListener('click', el.clickOutsideEvent);
      },
    }
  }
};
</script>