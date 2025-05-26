// n8n Process Tasks 노드용 수정된 JavaScript 코드
// "Code doesn't return items properly" 오류 해결

// 방법 1: 기본 item 처리 (권장)
return $input.all().map(item => ({
  json: {
    ...item.json,
    myNewField: 1,
    processed: true,
    timestamp: new Date().toISOString()
  }
}));

/* 
// 방법 2: 조건부 처리
return $input.all().map(item => ({
  json: {
    ...item.json,
    myNewField: item.json.someCondition ? 1 : 0,
    processed: true
  }
}));

// 방법 3: 복잡한 처리 로직
const outputItems = [];

for (const item of $input.all()) {
  outputItems.push({
    json: {
      ...item.json,
      myNewField: 1,
      processedAt: new Date().toISOString(),
      itemIndex: outputItems.length
    }
  });
}

console.log('Processed items:', outputItems.length);
return outputItems;
*/

// 핵심 포인트:
// 1. 항상 새로운 객체를 반환
// 2. ...item.json으로 기존 데이터 보존
// 3. 원본 item을 직접 수정하지 않음
// 4. console.log()로 디버깅 가능