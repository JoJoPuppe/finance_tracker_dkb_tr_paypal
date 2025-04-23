<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center">
     
    </header>

    <!-- Main Layout: Side Panels and Content -->
    <div class="flex flex-col md:flex-row gap-x-2 h-full overflow-hidden">
      <!-- Side Panel with Rules List -->
      <div class="w-1/8">
        <h2 class="text-xl font-bold text-gray-600 mb-2">Rules</h2>
        <div class="border-r border-r-black py-4 overflow-auto h-[calc(100vh-110px)]">
          <rule-list
            :categories="categories"
            @select-rule="handleRuleSelect"
            @edit-rule="handleEditRule"
            @delete-rule="handleDeleteRule"
            @revert-rule="handleRevertRule"
          />
        </div>
      </div>

      <!-- Side Panel with Categories List -->
      <div class="w-1/6">
        <h2 class="text-xl font-bold text-gray-600 mb-2">Categories</h2>
        <div class="border-r border-r-black p-1 overflow-auto h-[calc(100vh-110px)]">
          <category-list
            :categories="rootCategories"
            @edit="editCategory"
            @delete="confirmDeleteCategory"
          />
        </div>
      </div>
      
      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Rule Application Results -->
        <div v-if="ruleApplyResult" class="bg-green-900 bg-opacity-30 border border-green-600 rounded-lg p-4 mb-4">
          <div class="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-500 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <p class="text-green-300">{{ ruleApplyResult }}</p>
          </div>
        </div>

        <!-- Loading indicator for rule application -->
        <div v-if="applyingRule" class="bg-purple-900 bg-opacity-20 border border-purple-600 rounded-lg p-4 mb-4 flex items-center">
          <svg class="animate-spin h-5 w-5 text-purple-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-purple-300">Applying rule to transactions...</p>
        </div>
    
        <!-- Record Preview -->
        <record-preview 
          :record="recordPreview" 
          :highlight-key="searchColumn"
        />
    
        <!-- Forms section - Row with Rule Form and Category Form -->
        <div class="flex flex-col lg:flex-row gap-4 mb-4">
          <!-- Rule Creation/Editing Form -->
          <div class="flex-1 bg-gray-800 bg-opacity-60 rounded-lg p-4 border border-gray-700">
            <h2 class="text-xl font-bold text-purple-400 mb-2">
              {{ currentEditRule ? 'Edit Rule' : 'Create Rule' }}
            </h2>
            <rule-form
              :available-columns="availableColumns"
              :categories="categories"
              :edit-rule="currentEditRule"
              @rule-created="handleRuleCreated"
              @rule-updated="handleRuleUpdated"
              @cancel-edit="cancelEdit"
              @error="handleRuleError"
            />
          </div>

          <!-- Category Creation/Editing Form - Always visible -->
          <div class="flex-1 bg-gray-800 bg-opacity-60 rounded-lg p-4 border border-gray-700">
            <h2 class="text-xl font-bold text-purple-400 mb-2">
              {{ categoryFormMode === 'create' ? 'Create Category' : 'Edit Category' }}
            </h2>
            <category-form
              :parent-categories="availableParents"
              :initial-data="categoryFormData"
              :is-edit-mode="categoryFormMode === 'edit'"
              :has-subcategories="categoryFormMode === 'edit' && hasSubcategories(categoryFormData.id)"
              @submit="categoryFormMode === 'create' ? createCategory($event) : updateCategory($event)"
              @close="resetCategoryForm"
            />
          </div>
        </div>

        <!-- Transactions by Category Section -->
        <div class="flex-1 overflow-hidden">
          <transactions 
            :categories="categories"
            :refresh-trigger="refreshTrigger"
          />
        </div>
      </div>
    </div>

    <!-- Toast notifications -->
    <Toast 
      :message="toast.message" 
      :type="toast.type" 
      :is-visible="toast.isVisible" 
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';
import axios from 'axios';

// Import modular components
import RuleSearch from './RuleSearch.vue';
import RecordPreview from './RecordPreview.vue';
import RuleForm from './RuleForm.vue';
import RuleList from './RuleList.vue';
import CategoryList from './CategoryList.vue';
import CategoryForm from './CategoryForm.vue';
import Toast from './Toast.vue';
import Transactions from './Transactions.vue';

export default {
  name: 'RulesEditor',
  components: { 
    RuleSearch,
    RecordPreview,
    RuleForm,
    RuleList,
    CategoryList,
    CategoryForm,
    Toast,
    Transactions
  },
  
  setup() {
    // Rule state variables
    const availableColumns = ref([]);
    const searchColumn = ref('');
    const recordPreview = ref(null);
    const categories = ref([]);
    const currentEditRule = ref(null);
    const ruleApplyResult = ref(null);
    const applyingRule = ref(false);
    const refreshTrigger = ref(0);
    
    // Category state variables
    const categoryFormMode = ref('create');
    const categoryFormData = ref({ name: '', parentId: null });
    
    // Toast notification
    const toast = reactive({
      isVisible: false,
      message: '',
      type: 'success'
    });
    
    // Computed
    const rootCategories = computed(() => {
      return categories.value.filter(category => !category.parent_id);
    });

    const availableParents = computed(() => {
      // Filter to only include top-level categories
      const topLevelCategories = categories.value.filter(cat => !cat.parent_id);
      
      if (categoryFormMode.value === 'edit') {
        // When editing, exclude the current category from parent options
        const currentCategoryId = categoryFormData.value.id;
        return topLevelCategories.filter(cat => {
          // Don't allow a category to be its own parent or child of its children
          return cat.id !== currentCategoryId && !isDescendantOf(cat.id, currentCategoryId);
        });
      }
      return topLevelCategories;
    });
    
    // Fetch initial data when component mounts
    onMounted(async () => {
      await Promise.all([fetchColumns(), fetchCategories()]);
    });
    
    // Fetch column data
    const fetchColumns = async () => {
      try {
        const response = await axios.get('/api/v1/transactions/columns');
        if (response.data.status === 'success') {
          availableColumns.value = response.data.data.columns;
        } else {
          showToast('Failed to load column data', 'error');
        }
      } catch (error) {
        console.error('Error fetching columns:', error);
        showToast('Failed to load column data', 'error');
      }
    };
    
    // Fetch categories data
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/v1/categories');
        if (response.data.status === 'success') {
          categories.value = response.data.data;
          organizeCategories();
        } else {
          showToast('Failed to load categories', 'error');
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
        showToast('Failed to load categories', 'error');
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

    // Category Management Methods
    const isDescendantOf = (categoryId, potentialAncestorId) => {
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

    const resetCategoryForm = () => {
      categoryFormMode.value = 'create';
      categoryFormData.value = { name: '', parentId: null };
    };

    const editCategory = (category) => {
      categoryFormMode.value = 'edit';
      categoryFormData.value = { 
        id: category.id,
        name: category.name,
        parentId: category.parent_id
      };
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
          resetCategoryForm();
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
          resetCategoryForm();
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

    const confirmDeleteCategory = (categoryId) => {
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
    
    // Apply a rule to all transactions
    const applyRule = async (ruleId) => {
      applyingRule.value = true;
      ruleApplyResult.value = null;
      
      try {
        const response = await axios.post(`/api/v1/transactions/apply-rule/${ruleId}`);
        if (response.data.status === 'success') {
          ruleApplyResult.value = response.data.message;
          showToast(response.data.message, 'success');
          refreshTrigger.value++;
        } else {
          showToast('Failed to apply rule to transactions', 'error');
        }
      } catch (error) {
        console.error('Error applying rule:', error);
        showToast(error.response?.data?.message || 'Failed to apply rule to transactions', 'error');
      } finally {
        applyingRule.value = false;
      }
    };

    // Revert a rule's effects on all transactions
    const revertRule = async (ruleId) => {
      applyingRule.value = true;
      ruleApplyResult.value = null;
      
      try {
        const response = await axios.post(`/api/v1/transactions/revert-rule/${ruleId}`);
        if (response.data.status === 'success') {
          ruleApplyResult.value = response.data.message;
          showToast(response.data.message, 'success');
          refreshTrigger.value++;
        } else {
          showToast('Failed to revert rule effects on transactions', 'error');
        }
      } catch (error) {
        console.error('Error reverting rule:', error);
        showToast(error.response?.data?.message || 'Failed to revert rule effects on transactions', 'error');
      } finally {
        applyingRule.value = false;
      }
    };
    
    // Handle rule selection from the side panel
    const handleRuleSelect = (rule) => {
      console.log('Selected rule:', rule);
    };
    
    // Handle rule edit request
    const handleEditRule = (rule) => {
      currentEditRule.value = rule;
      showToast('Editing rule: ' + rule.name, 'info');
    };
    
    // Cancel editing
    const cancelEdit = () => {
      currentEditRule.value = null;
    };
    
    // Handle rule deletion
    const handleDeleteRule = (ruleId, errorMessage = null) => {
      if (errorMessage) {
        showToast(errorMessage, 'error');
      } else {
        showToast('Rule deleted successfully', 'success');
        if (currentEditRule.value && currentEditRule.value.id === ruleId) {
          currentEditRule.value = null;
        }
      }
    };

    // Handle rule revert
    const handleRevertRule = (ruleId) => {
      revertRule(ruleId);
    };
    
    // Handle search result from RuleSearch component
    const handleSearchResult = (result) => {
      recordPreview.value = result;
    };
    
    // Handle search error from RuleSearch component
    const handleSearchError = (error) => {
      showToast(error, 'error');
    };
    
    // Handle successful rule creation
    const handleRuleCreated = (rule) => {
      showToast('Rule created successfully', 'success');
      // Reset any current edit state
      currentEditRule.value = null;
      applyRule(rule.id);
    };
    
    // Handle successful rule update
    const handleRuleUpdated = (rule) => {
      showToast('Rule updated successfully', 'success');
      currentEditRule.value = null;
      applyRule(rule.id);
    };
    
    // Handle rule creation/update error
    const handleRuleError = (error) => {
      showToast(error, 'error');
    };
    
    // Display toast notification
    const showToast = (message, type = 'success') => {
      toast.message = message;
      toast.type = type;
      toast.isVisible = true;
      setTimeout(() => (toast.isVisible = false), 3000);
    };
    
    return {
      // Rule data
      availableColumns,
      searchColumn,
      recordPreview,
      currentEditRule,
      ruleApplyResult,
      applyingRule,
      refreshTrigger,
      
      // Category data
      categories,
      rootCategories,
      categoryFormMode,
      categoryFormData,
      availableParents,
      
      // Toast
      toast,
      
      // Rule methods
      handleRuleSelect,
      handleEditRule,
      handleDeleteRule,
      handleRevertRule,
      handleSearchResult,
      handleSearchError,
      handleRuleCreated,
      handleRuleUpdated,
      handleRuleError,
      cancelEdit,
      
      // Category methods
      editCategory,
      createCategory,
      updateCategory,
      confirmDeleteCategory,
      deleteCategory,
      hasSubcategories,
      resetCategoryForm,
      
      // Common methods
      showToast,
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
