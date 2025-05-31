#!/usr/bin/env python3
"""Run 200-command test in chunks to avoid timeouts."""

import json
import time
import logging
from test_200_complex_commands import Comprehensive200CommandTest

logging.basicConfig(level=logging.ERROR)

def run_chunked_test(chunk_size=25):
    """Run test in chunks to avoid timeouts."""
    print("🧪 RUNNING 200-COMMAND TEST IN CHUNKS")
    print("=" * 50)
    
    tester = Comprehensive200CommandTest()
    commands = tester.get_200_complex_commands()
    
    all_results = []
    chunk_results = {}
    
    total_chunks = (len(commands) + chunk_size - 1) // chunk_size
    
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(commands))
        chunk_commands = commands[start_idx:end_idx]
        
        print(f"\n📦 Chunk {chunk_idx + 1}/{total_chunks}: Commands {start_idx + 1}-{end_idx}")
        
        chunk_successes = 0
        chunk_start_time = time.time()
        
        for i, (command, category, complexity, expected) in enumerate(chunk_commands):
            global_idx = start_idx + i + 1
            
            # Execute command
            result = tester.game.process_command(command)
            success = result.get('success', False)
            message = result.get('message', '')
            
            if success:
                chunk_successes += 1
                print(f"  {global_idx:3d}. ✅ [{category}] '{command[:40]}...'")
            else:
                error_preview = message[:30].replace('\n', ' ')
                print(f"  {global_idx:3d}. ❌ [{category}] '{command[:40]}...' → {error_preview}...")
            
            # Store result
            result_data = {
                'index': global_idx,
                'command': command,
                'category': category,
                'complexity': complexity,
                'success': success,
                'message': message,
                'expected': expected
            }
            all_results.append(result_data)
        
        chunk_time = time.time() - chunk_start_time
        chunk_rate = (chunk_successes / len(chunk_commands)) * 100
        
        chunk_results[f"chunk_{chunk_idx + 1}"] = {
            'commands': len(chunk_commands),
            'successes': chunk_successes,
            'success_rate': chunk_rate,
            'time': chunk_time
        }
        
        print(f"  Chunk Result: {chunk_successes}/{len(chunk_commands)} ({chunk_rate:.1f}%) in {chunk_time:.1f}s")
    
    # Overall analysis
    total_successes = sum(1 for r in all_results if r['success'])
    overall_rate = (total_successes / len(all_results)) * 100
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Total Commands: {len(all_results)}")
    print(f"   Successful: {total_successes}")
    print(f"   Success Rate: {overall_rate:.1f}%")
    
    # Category analysis
    categories = {}
    for result in all_results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'successes': 0}
        categories[cat]['total'] += 1
        if result['success']:
            categories[cat]['successes'] += 1
    
    print(f"\n📈 CATEGORY BREAKDOWN:")
    for cat, stats in sorted(categories.items()):
        rate = (stats['successes'] / stats['total']) * 100
        print(f"   {cat.title()}: {stats['successes']}/{stats['total']} ({rate:.1f}%)")
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"chunked_test_results_{timestamp}.json"
    
    output_data = {
        'metadata': {
            'timestamp': timestamp,
            'total_commands': len(all_results),
            'total_successes': total_successes,
            'overall_success_rate': overall_rate,
            'chunk_size': chunk_size,
            'total_chunks': total_chunks
        },
        'chunk_summary': chunk_results,
        'category_analysis': categories,
        'detailed_results': all_results
    }
    
    with open(results_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return overall_rate, results_file

if __name__ == "__main__":
    rate, file = run_chunked_test(chunk_size=20)
    print(f"\n🎯 Final Score: {rate:.1f}%")