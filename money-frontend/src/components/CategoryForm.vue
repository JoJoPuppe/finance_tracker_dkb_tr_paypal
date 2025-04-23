<template>
  <form @submit.prevent="handleSubmit" class="space-y-5">
    <div>
      <label for="name" class="block text-sm font-medium text-gray-300 mb-1">Category Name</label>
      <div class="relative">
        <input
          id="name"
          v-model="formData.name"
          type="text"
          class="block w-full rounded-md bg-gray-800 border border-gray-700 text-white py-2 px-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          :class="{ 'border-red-500': errorMessages.name }"
          required
          autocomplete="off"
          ref="nameInput"
        />
        <div v-if="isValidating" class="absolute right-2 top-2">
          <div class="loader-sm border-t-2 border-purple-400 rounded-full w-4 h-4 animate-spin"></div>
        </div>
      </div>
      <p v-if="errorMessages.name" class="text-red-400 text-sm mt-1 animate-fade-in">
        {{ errorMessages.name }}
      </p>
    </div>
    
    <div>
      <label for="parent" class="block text-sm font-medium text-gray-300 mb-1">Parent Category</label>
      <select
        id="parent"
        v-model="formData.parentId"
        class="block w-full rounded-md bg-gray-800 border border-gray-700 text-white py-2 px-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
        :class="{ 'border-red-500': errorMessages.parentId, 'opacity-60 cursor-not-allowed': hasSubcategories }"
        :disabled="hasSubcategories"
      >
        <option value="">None (Top-level category)</option>
        <option v-for="category in parentCategories" :key="category.id" :value="category.id">
          {{ category.name }}
        </option>
      </select>
      <p v-if="errorMessages.parentId" class="text-red-400 text-sm mt-1 animate-fade-in">
        {{ errorMessages.parentId }}
      </p>
      <p v-if="hasSubcategories" class="text-amber-400 text-sm mt-1 animate-fade-in">
        Categories with subcategories must remain at the top level to prevent nesting beyond one level.
      </p>
      <p v-else-if="parentCategories.length === 0" class="text-gray-400 text-xs mt-1">
        No other categories available to use as parent.
      </p>
    </div>
    
    <div class="flex space-x-3 pt-2">
      <button
        type="button"
        @click="$emit('close')"
        class="flex-1 py-2 px-4 bg-gray-700 text-white font-medium rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
      >
        Cancel
      </button>
      <button
        type="submit"
        :disabled="isSubmitting"
        class="flex-1 py-2 px-4 bg-purple-600 text-white font-medium rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 flex justify-center items-center"
        :class="{ 'opacity-75 cursor-not-allowed': isSubmitting }"
      >
        <span v-if="isSubmitting" class="loader-sm border-t-2 border-white rounded-full w-4 h-4 animate-spin mr-2"></span>
        {{ isEditMode ? 'Update Category' : 'Create Category' }}
      </button>
    </div>
  </form>
</template>

<script>
import { ref, reactive, watch, nextTick, onMounted } from 'vue';

export default {
  name: 'CategoryForm',
  props: {
    parentCategories: {
      type: Array,
      required: true,
    },
    initialData: {
      type: Object,
      default: () => ({ name: '', parentId: '' }),
    },
    isEditMode: {
      type: Boolean,
      default: false,
    },
    hasSubcategories: {
      type: Boolean,
      default: false,
    }
  },
  emits: ['submit', 'close'],
  setup(props, { emit }) {
    const formData = reactive({ ...props.initialData });
    const errorMessages = reactive({});
    const isSubmitting = ref(false);
    const isValidating = ref(false);
    const nameInput = ref(null);
    
    // Focus on the name input when component mounts
    onMounted(() => {
      nextTick(() => {
        if (nameInput.value) {
          nameInput.value.focus();
        }
      });
    });
    
    // Reset form data when initialData changes
    watch(() => props.initialData, (newVal) => {
      Object.assign(formData, newVal);
    }, { deep: true });
    
    const validateForm = () => {
      errorMessages.name = '';
      errorMessages.parentId = '';
      
      // Name validation
      if (!formData.name || formData.name.trim() === '') {
        errorMessages.name = 'Category name is required';
        return false;
      }
      
      // Check for duplicate names under the same parent
      const sameLevelCategories = props.parentCategories.filter(cat => 
        cat.parent_id === formData.parentId && cat.id !== formData.id
      );
      
      if (sameLevelCategories.some(cat => cat.name.toLowerCase() === formData.name.toLowerCase())) {
        errorMessages.name = 'A category with this name already exists at this level';
        return false;
      }
      
      return true;
    };
    
    const handleSubmit = async () => {
      isValidating.value = true;
      await new Promise(resolve => setTimeout(resolve, 300)); // Small delay for validation UX
      isValidating.value = false;
      
      if (validateForm()) {
        isSubmitting.value = true;
        
        try {
          emit('submit', { 
            id: formData.id,
            name: formData.name.trim(), 
            parentId: formData.parentId || null
          });
          emit('close');
        } finally {
          isSubmitting.value = false;
        }
      }
    };
    
    return {
      formData,
      errorMessages,
      isSubmitting,
      isValidating,
      nameInput,
      handleSubmit,
    };
  }
};
</script>

<style scoped>
.loader-sm {
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>