<template>
  <div v-if="record" class="bg-gray-800 bg-opacity-40 rounded-lg p-6 mb-6">
    <h2 class="text-xl font-semibold text-purple-300 mb-4">Record Preview</h2>
    <div class="bg-gray-700 p-4 rounded-lg">
      <div v-for="(value, key) in record" :key="key" class="mb-2 flex">
        <span class="text-gray-400 font-medium w-1/3">{{ key }}:</span>
        <span :class="{'text-purple-300 font-semibold': key === highlightKey}">{{ value }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RecordPreview',
  props: {
    record: {
      type: Object,
      required: false,
      default: null
    },
    highlightKey: {
      type: String,
      required: false,
      default: ''
    }
  }
};
</script>