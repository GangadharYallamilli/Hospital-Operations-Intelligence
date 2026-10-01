# =========================================================
# GEMINI API KEY MANAGER
# =========================================================
#
# Supports 5 Gemini API keys.
#
# Key rotation:
#
# Key 1
#   ↓ failure
# Key 2
#   ↓ failure
# Key 3
#   ↓ failure
# Key 4
#   ↓ failure
# Key 5
#
# If all keys fail, returns None.
# The RAG answer generator then uses its local fallback.
#
# =========================================================

import os
import time

from google import genai


class GeminiKeyManager:

    def __init__(self):

        self.keys = [
            os.getenv("GEMINI_API_KEY_1"),
            os.getenv("GEMINI_API_KEY_2"),
            os.getenv("GEMINI_API_KEY_3"),
            os.getenv("GEMINI_API_KEY_4"),
            os.getenv("GEMINI_API_KEY_5"),
        ]

        # Remove empty keys
        self.keys = [
            key.strip()
            for key in self.keys
            if key and key.strip()
        ]

        # Start with first available key
        self.current_index = 0

        # Failed keys are temporarily skipped
        self.cooldown_until = {}


    # =====================================================
    # CHECK WHETHER ANY KEY EXISTS
    # =====================================================

    def available(self):

        return len(self.keys) > 0


    # =====================================================
    # GET CURRENTLY USABLE KEYS
    # =====================================================

    def _usable_key_indices(self):

        now = time.time()

        usable = []

        for index in range(len(self.keys)):

            cooldown = self.cooldown_until.get(
                index,
                0
            )

            if cooldown <= now:

                usable.append(index)

        return usable


    # =====================================================
    # GENERATE GEMINI RESPONSE
    # =====================================================

    def generate(
        self,
        prompt,
        model_name="gemini-3.6-flash",
        cooldown_seconds=60
    ):

        if not self.available():

            print(
                "No Gemini API keys configured."
            )

            return None


        usable_indices = (
            self._usable_key_indices()
        )


        if not usable_indices:

            print(
                "All Gemini API keys are currently "
                "in cooldown."
            )

            return None


        # =================================================
        # ROTATION ORDER
        # =================================================

        ordered_indices = []

        for offset in range(len(self.keys)):

            index = (
                self.current_index + offset
            ) % len(self.keys)

            if index in usable_indices:

                ordered_indices.append(index)


        # =================================================
        # TRY EACH KEY
        # =================================================

        for index in ordered_indices:

            try:

                api_key = self.keys[index]


                # -----------------------------------------
                # Create Gemini client
                # -----------------------------------------

                client = genai.Client(
                    api_key=api_key
                )


                # -----------------------------------------
                # Generate response
                # -----------------------------------------

                response = client.models.generate_content(

                    model=model_name,

                    contents=prompt

                )


                # -----------------------------------------
                # Read response
                # -----------------------------------------

                if response is not None:

                    response_text = getattr(
                        response,
                        "text",
                        None
                    )


                    if (
                        response_text
                        and response_text.strip()
                    ):

                        # Keep successful key
                        # as the preferred key
                        self.current_index = index

                        return response_text.strip()


                # Empty response
                self.cooldown_until[index] = (
                    time.time()
                    + cooldown_seconds
                )


            except Exception as error:

                print(
                    f"Gemini key {index + 1} failed: "
                    f"{repr(error)}"
                )


                # -----------------------------------------
                # Temporarily skip failed key
                # -----------------------------------------

                self.cooldown_until[index] = (
                    time.time()
                    + cooldown_seconds
                )

                continue


        # =================================================
        # ALL KEYS FAILED
        # =================================================

        print(
            "All Gemini API keys failed."
        )

        return None


# =========================================================
# SHARED MANAGER INSTANCE
# =========================================================

gemini_manager = GeminiKeyManager()