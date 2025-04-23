<template>
  <div class="h-full">
    <header class="mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center">
      <h1 class="text-3xl font-bold text-purple-400 mb-4 sm:mb-0">Category Editor</h1>
      <button 
        v-if="!showForm"
        @click="openCreateForm" 
        class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md flex items-center transition duration-200"
      >
        <span class="mr-2">+</span> New Category
      </button>
      <button
        v-else
        @click="closeForm"
        class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md flex items-center transition duration-200"
      >
        <span class="mr-2">×</span> Cancel
      </button>
    </header>

    <!-- Form Section Above Category List -->
    <div v-if="showForm" class="mb-8 bg-gray-800 bg-opacity-60 rounded-lg p-6 border border-gray-700">
      <h2 class="text-xl font-bold text-purple-400 mb-4">
        {{ formMode === 'create' ? 'Create New Category' : 'Edit Category' }}
      </h2>
      <CategoryForm
        :parent-categories="availableParents"
        :initial-data="formData"
        :is-edit-mode="formMode === 'edit'"
        :has-subcategories="formMode === 'edit' && hasSubcategories(formData.id)"
        @submit="formMode === 'create' ? createCategory($event) : updateCategory($event)"
        @close="closeForm"
      />
    </div>

    <div v-if="isLoading" class="flex justify-center items-center py-16">
      <div class="loader border-t-4 border-purple-400 rounded-full w-10 h-10 animate-spin"></div>
    </div>

    <div v-else-if="error" class="bg-red-900 bg-opacity-25 border border-red-500 rounded-lg p-4 mb-6">
      <p class="text-red-400">{{ error }}</p>
      <button @click="fetchCategories" class="text-white underline mt-2">Retry</button>
    </div>

    <div v-else-if="categories.length === 0" class="flex flex-col items-center justify-center py-16 bg-gray-800 bg-opacity-40 rounded-lg">
      <p class="text-gray-400 mb-4">No categories found</p>
      <button 
        @click="openCreateForm" 
        class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md"
      >
        Create your first category
      </button>
    </div>

    <div v-else class="bg-gray-800 bg-opacity-40 rounded-lg p-4">
      <CategoryList
        :categories="rootCategories"
        @edit="editCategory"
        @delete="confirmDelete"
      />
    </div>

    <Toast 
      :message="toast.message" 
      :type="toast.type" 
      :is-visible="toast.isVisible" 
    />
  </div>
</template>

<script>
import axios from 'axios';
import { ref, reactive, computed } from 'vue';
import CategoryList from './CategoryList.vue';
import CategoryForm from './CategoryForm.vue';
import Toast from './Toast.vue';

export default {
  name: 'CategoryEditor',
  components: { CategoryList, CategoryForm, Toast },
  setup() {
    // State
    const categories = ref([]);
    const showForm = ref(false);
    const toast = reactive({
      isVisible: false,
      message: '',
      type: 'success'
    });
    const formMode = ref('create');
    const formData = ref({ name: '', parentId: null });
    const isLoading = ref(true);
    const error = ref(null);

    // Computed
    const rootCategories = computed(() => {
      return categories.value.filter(category => !category.parent_id);
    });

    const availableParents = computed(() => {
      // Filter to only include top-level categories
      const topLevelCategories = categories.value.filter(cat => !cat.parent_id);
      
      if (formMode.value === 'edit') {
        // When editing, exclude the current category from parent options
        const currentCategoryId = formData.value.id;
        return topLevelCategories.filter(cat => {
          // Don't allow a category to be its own parent or child of its children
          return cat.id !== currentCategoryId && !isDescendantOf(cat.id, currentCategoryId);
        });
      }
      return topLevelCategories;
    });

    // Methods
    const fetchCategories = async () => {
      isLoading.value = true;
      error.value = null;
      try {
        const response = await axios.get('/api/v1/categories');
        if (response.data.status === 'success' && Array.isArray(response.data.data)) {
          categories.value = response.data.data;
          organizeCategories();
        } else {
          console.error('Unexpected API response:', response.data);
          error.value = 'Invalid data received from the server';
        }
      } catch (err) {
        console.error('API error:', err);
        error.value = 'Failed to fetch categories. Please try again.';
      } finally {
        isLoading.value = false;
      }
    };

    const organizeCategories = () => {
      // This method ensures each category has a subcategories array
      categories.value.forEach(category => {
        if (!category.subcategories) {
          category.subcategories = [];
        }
      });
    };

    const isDescendantOf = (categoryId, potentialAncestorId) => {
      // Check if categoryId is a descendant of potentialAncestorId
      const category = categories.value.find(c => c.id === categoryId);
      if (!category) return false;
      
      if (category.parent_id === potentialAncestorId) return true;
      if (category.parent_id) {
        return isDescendantOf(category.parent_id, potentialAncestorId);
      }
      return false;
    };

    const hasSubcategories = (categoryId) => {
      const category = categories.value.find(c => c.id === categoryId);
      return category && category.subcategories && category.subcategories.length > 0;
    };

    const openCreateForm = () => {
      formMode.value = 'create';
      formData.value = { name: '', parentId: null };
      showForm.value = true;
    };

    const closeForm = () => {
      showForm.value = false;
    };

    const editCategory = (category) => {
      formMode.value = 'edit';
      formData.value = { 
        id: category.id,
        name: category.name,
        parentId: category.parent_id
      };
      showForm.value = true;
      console.log('Edit category triggered for:', category.name);
    };

    const createCategory = async (categoryData) => {
      try {
        const response = await axios.post('/api/v1/categories', {
          name: categoryData.name,
          parent_id: categoryData.parentId || null
        });
        
        if (response.data.status === 'success') {
          showToast('Category created successfully', 'success');
          await fetchCategories(); // Refresh the list
          closeForm();
        } else {
          showToast('Failed to create category', 'error');
        }
      } catch (err) {
        console.error('Error creating category:', err);
        showToast(
          err.response?.data?.message || 'Failed to create category', 
          'error'
        );
      }
    };

    const updateCategory = async (categoryData) => {
      try {
        const response = await axios.put(`/api/v1/categories/${categoryData.id}`, {
          name: categoryData.name,
          parent_id: categoryData.parentId || null
        });
        
        if (response.data.status === 'success') {
          showToast('Category updated successfully', 'success');
          await fetchCategories(); // Refresh the list
          closeForm();
        } else {
          showToast('Failed to update category', 'error');
        }
      } catch (err) {
        console.error('Error updating category:', err);
        showToast(
          err.response?.data?.message || 'Failed to update category', 
          'error'
        );
      }
    };

    const confirmDelete = (categoryId) => {
      if (confirm('Are you sure you want to delete this category? This action cannot be undone.')) {
        deleteCategory(categoryId);
      }
    };

    const deleteCategory = async (categoryId) => {
      try {
        const response = await axios.delete(`/api/v1/categories/${categoryId}`);
        
        if (response.data.status === 'success') {
          categories.value = categories.value.filter(cat => cat.id !== categoryId);
          showToast('Category deleted successfully', 'success');
        } else {
          showToast('Failed to delete category', 'error');
        }
      } catch (err) {
        console.error('Error deleting category:', err);
        const errorMessage = err.response?.data?.message || 'Failed to delete category';
        showToast(errorMessage, 'error');
      }
    };

    const showToast = (message, type = 'success') => {
      toast.message = message;
      toast.type = type;
      toast.isVisible = true;
      setTimeout(() => (toast.isVisible = false), 3000);
    };

    // Fetch categories on mount
    fetchCategories();

    return {
      categories,
      rootCategories,
      showForm,
      toast,
      formMode,
      formData,
      isLoading,
      error,
      availableParents,
      fetchCategories,
      openCreateForm,
      closeForm,
      editCategory,
      createCategory,
      updateCategory,
      confirmDelete,
      deleteCategory,
      showToast,
      hasSubcategories
    };
  }
};
</script>

<style scoped>
.loader {
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #9f7aea;
}
</style>