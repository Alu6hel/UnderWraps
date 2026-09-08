/**
 * ==============================================================================
 * UnderWraps Sovereign Android JNI Native Bridge
 * Bridges Android NDK / ARM64 with Pure ALU Core & Kybalion Engine
 * 
 * Sole Founder, Originator & Chief Architect: David Anthony Jones ("Alu")
 * License: Alumungandr Master Charter (Copyright © 2026 Alumungandr)
 * ==============================================================================
 */

#include <jni.h>
#include <string>
#include <android/log.h>

#define LOG_TAG "UnderWrapsJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" {

// C-ABI exports from ALU compiled libkybalion_core.so and libunderwraps_core.so
extern bool underwraps_validate_file_boundary(uint32_t file_size_bytes);
extern void underwraps_process_voice_frame(const float* in_pcm, float* out_pcm, uint32_t len);

JNIEXPORT jboolean JNICALL
Java_com_alumungandr_underwraps_server_ServerService_startNativeServer(JNIEnv* env, jobject thiz) {
    LOGI("[UnderWraps JNI] Initializing Native Server Engine & Kybalion DB...");
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_com_alumungandr_underwraps_server_ServerService_stopNativeServer(JNIEnv* env, jobject thiz) {
    LOGI("[UnderWraps JNI] Stopping Native Server Engine...");
    return JNI_TRUE;
}

JNIEXPORT jboolean JNICALL
Java_com_alumungandr_underwraps_client_NativeBridge_validate150MBGuard(JNIEnv* env, jobject thiz, jlong fileSize) {
    // 150MB = 157,286,400 bytes
    return (fileSize > 0 && fileSize <= 157286400) ? JNI_TRUE : JNI_FALSE;
}

}
