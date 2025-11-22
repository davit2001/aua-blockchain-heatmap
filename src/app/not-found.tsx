"use client";

import SomethingWentWrongIcon from "@/assets/something-went-wrong.svg";

const ErrorPage = () => (
    <div className="px-4 mx-auto w-full h-screen justify-center max-w-container flex flex-col items-center desktop:gap-10 tablet:gap-8 mobile:gap-[60px]">
        <SomethingWentWrongIcon className="w-full h-auto"/>
        <div className="flex flex-col tablet:gap-6 mobile:gap-4">
            <h1 className="desktop:text-[56px] tablet:text-[40px] mobile:text-[32px] text-primary text-center font-bold">
                Page Not Found
            </h1>
            <p className="text-center text-tertiary desktop:text-2xl tablet:text-xl mobile:text-sm">
                Oops! The page you are looking for does not exist. It may have been moved, deleted, or never existed at all.
            </p>
        </div>
    </div>
);

export default ErrorPage;
