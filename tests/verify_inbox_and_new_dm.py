import asyncio
import json
import time
import base64
import os
import urllib.request
import websockets

ARTIFACTS_DIR = "/home/davidalujones/.gemini/antigravity/brain/23f511ed-0b21-4a49-bbe3-0e7f15a457c4"

async def cdp_eval(ws, expr):
    msg_id = int(time.time() * 1000) % 1000000
    req = {
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        }
    }
    await ws.send(json.dumps(req))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == msg_id:
            res = resp.get("result", {}).get("result", {})
            if "value" in res:
                return res["value"]
            return res

import subprocess

def take_screenshot(filename):
    filepath = os.path.join(ARTIFACTS_DIR, filename)
    cmd = f"adb -s 100.115.92.2:5555 exec-out screencap -p > '{filepath}'"
    subprocess.run(cmd, shell=True, check=True)
    print(f" [SCREENSHOT] Saved: {filepath}")

async def main():
    req = urllib.request.urlopen("http://localhost:9223/json")
    targets = json.loads(req.read().decode("utf-8"))
    page = next(t for t in targets if t.get("type") == "page")
    ws_url = page["webSocketDebuggerUrl"]
    print(f"Connecting to CDP: {ws_url}")

    async with websockets.connect(ws_url) as ws:
        # Step 1: Ensure in Chat Screen
        init_state = await cdp_eval(ws, """
            (async () => {
                if (typeof window.__underwrapsDevBypass === 'function') {
                    window.__underwrapsDevBypass('alu');
                }
                if (typeof returnToInbox === 'function') {
                    await returnToInbox();
                }
                const layout = document.getElementById('messenger-layout') || document.querySelector('.messenger-layout');
                return {
                    chatScreenVisible: !document.getElementById('chat-screen').classList.contains('hidden'),
                    layoutClasses: layout ? layout.className : '',
                    activeConvId: window.activeConvId || null,
                    convCount: (window.allConversationItems || []).length
                };
            })()
        """)
        print(f"Step 1 - Initial State: {init_state}")

        # Step 2: Test Return to All Chats (inbox)
        inbox_state = await cdp_eval(ws, """
            (async () => {
                if (typeof returnToInbox === 'function') {
                    await returnToInbox();
                }
                const layout = document.querySelector('.messenger-layout');
                return {
                    layoutClasses: layout ? layout.className : '',
                    isViewInbox: layout ? layout.classList.contains('view-inbox') : false,
                    isViewChat: layout ? layout.classList.contains('view-chat') : false,
                    activeConvId: window.activeConvId || null,
                    peerNameText: document.getElementById('chat-peer-name')?.textContent
                };
            })()
        """)
        print(f"Step 2 - Return to Inbox Immediate: {inbox_state}")
        assert inbox_state["isViewInbox"], "Layout must have view-inbox class!"
        assert not inbox_state["isViewChat"], "Layout must NOT have view-chat class!"
        assert inbox_state.get("activeConvId") is None, "activeConvId must be null in inbox!"

        # Wait 800ms to verify no rogue timer or sync re-selected a chat
        await asyncio.sleep(0.8)
        after_wait = await cdp_eval(ws, """
            (() => {
                const layout = document.querySelector('.messenger-layout');
                return {
                    layoutClasses: layout ? layout.className : '',
                    isViewInbox: layout ? layout.classList.contains('view-inbox') : false,
                    isViewChat: layout ? layout.classList.contains('view-chat') : false,
                    activeConvId: window.activeConvId || null
                };
            })()
        """)
        print(f"Step 2.1 - Return to Inbox After Wait (no trap): {after_wait}")
        assert after_wait["isViewInbox"], "Layout must still have view-inbox class after wait!"
        assert not after_wait["isViewChat"], "Auto-select trap must NOT re-activate chat!"

        take_screenshot("live_all_chats_inbox_view.png")

        # Step 3: Test Selecting a conversation
        select_state = await cdp_eval(ws, """
            (async () => {
                const list = (typeof allConversationItems !== 'undefined') ? allConversationItems : [];
                if (list.length > 0) {
                    await selectConversation(list[0]);
                }
                const layout = document.querySelector('.messenger-layout');
                return {
                    isViewChat: layout ? layout.classList.contains('view-chat') : false,
                    activeConvId: (typeof activeConvId !== 'undefined') ? activeConvId : null,
                    peerNameText: document.getElementById('chat-peer-name')?.textContent,
                    callBtnHidden: document.getElementById('btn-start-call')?.classList.contains('hidden')
                };
            })()
        """)
        print(f"Step 3 - Select Conversation: {select_state}")
        assert select_state["isViewChat"], "Layout must transition to view-chat!"
        assert select_state.get("activeConvId") is not None, "activeConvId must be set!"
        assert not select_state["callBtnHidden"], "Call button must be visible in active chat!"

        take_screenshot("live_active_chat_view.png")

        # Step 4: Test clicking back button in header
        back_click_state = await cdp_eval(ws, """
            (() => {
                const backBtn = document.getElementById('btn-back-to-inbox');
                if (backBtn) backBtn.click();
                const layout = document.querySelector('.messenger-layout');
                return {
                    isViewInbox: layout ? layout.classList.contains('view-inbox') : false,
                    activeConvId: (typeof activeConvId !== 'undefined') ? activeConvId : null
                };
            })()
        """)
        print(f"Step 4 - Back Button Click: {back_click_state}")
        assert back_click_state["isViewInbox"], "Clicking back button must return to view-inbox!"
        assert back_click_state.get("activeConvId") is None, "activeConvId must be cleared!"

        # Step 5: Test New DM Modal
        modal_state = await cdp_eval(ws, """
            (async () => {
                if (typeof openNewChatModal === 'function') await openNewChatModal();
                const modal = document.getElementById('modal-new-chat');
                const userList = document.getElementById('new-chat-user-list');
                const searchInput = document.getElementById('new-chat-search-input');
                const directBtn = document.getElementById('btn-create-dm-direct');
                
                return {
                    modalVisible: !modal.classList.contains('hidden'),
                    userCardsCount: userList ? userList.children.length : 0,
                    hasDirectBtn: !!directBtn,
                    directBtnText: directBtn ? directBtn.textContent : ''
                };
            })()
        """)
        print(f"Step 5 - Open New DM Modal: {modal_state}")
        assert modal_state["modalVisible"], "New DM modal must be visible!"
        assert modal_state["hasDirectBtn"], "Direct Chat button must exist!"

        take_screenshot("live_new_dm_modal_view.png")

        # Step 6: Test Typing in New DM and Starting Direct Message with @satoshi
        dm_test_state = await cdp_eval(ws, """
            (async () => {
                const input = document.getElementById('new-chat-search-input');
                input.value = 'satoshi';
                filterNewChatUsers();
                const directBtn = document.getElementById('btn-create-dm-direct');
                const btnLabel = directBtn ? directBtn.textContent : '';

                // Trigger direct message creation
                await startDirectMessageWithUsername('satoshi');
                
                const layout = document.querySelector('.messenger-layout');
                const modal = document.getElementById('modal-new-chat');
                return {
                    btnLabelAfterType: btnLabel,
                    modalClosed: modal.classList.contains('hidden'),
                    isViewChat: layout.classList.contains('view-chat'),
                    peerUsername: (typeof activePeer !== 'undefined' && activePeer) ? activePeer.username : null,
                    activeConvId: (typeof activeConvId !== 'undefined') ? activeConvId : null
                };
            })()
        """)
        print(f"Step 6 - Direct Message with @satoshi: {dm_test_state}")
        assert dm_test_state["btnLabelAfterType"] == "Chat @satoshi", "Button text must dynamically show Chat @satoshi!"
        assert dm_test_state["modalClosed"], "Modal must close on DM start!"
        assert dm_test_state["isViewChat"], "Must transition to view-chat for @satoshi!"
        assert dm_test_state["peerUsername"] == "satoshi", "Active peer username must be satoshi!"

        take_screenshot("live_dm_with_satoshi_active.png")

        # Step 7: Verify Dev Nav Positioning
        dev_nav_check = await cdp_eval(ws, """
            (() => {
                const nav = document.getElementById('dev-floating-nav');
                if (!nav) return { exists: false };
                const style = window.getComputedStyle(nav);
                const callBtn = document.getElementById('btn-start-call');
                const callRect = callBtn ? callBtn.getBoundingClientRect() : null;
                const navRect = nav.getBoundingClientRect();
                
                // Check if rects overlap
                let overlaps = false;
                if (callRect) {
                    overlaps = !(navRect.right < callRect.left || 
                                 navRect.left > callRect.right || 
                                 navRect.bottom < callRect.top || 
                                 navRect.top > callRect.bottom);
                }
                return {
                    exists: true,
                    bottom: style.bottom,
                    left: style.left,
                    overlapsCallBtn: overlaps
                };
            })()
        """)
        print(f"Step 7 - Dev Nav Position & Overlap Check: {dev_nav_check}")
        assert not dev_nav_check.get("overlapsCallBtn", False), "Dev Nav MUST NOT overlap Call button!"

        print("\n [ALL CHECKS PASSED] Return to all chats, New DM creation, and UI polish completely verified!\n")

if __name__ == "__main__":
    asyncio.run(main())
